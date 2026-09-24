package ua.kostia.spookyprice;

import com.google.gson.Gson;
import com.google.gson.GsonBuilder;
import com.google.gson.JsonArray;
import com.google.gson.JsonObject;
import net.fabricmc.api.ClientModInitializer;
import net.fabricmc.fabric.api.client.event.lifecycle.v1.ClientTickEvents;
import net.fabricmc.fabric.api.client.keybinding.v1.KeyBindingHelper;
import net.fabricmc.fabric.api.client.message.v1.ClientSendMessageEvents;
import net.fabricmc.loader.api.FabricLoader;
import net.minecraft.client.MinecraftClient;
import net.minecraft.client.gui.screen.ingame.HandledScreen;
import net.minecraft.client.option.KeyBinding;
import net.minecraft.client.util.InputUtil;
import net.minecraft.item.Item;
import net.minecraft.item.ItemStack;
import net.minecraft.item.tooltip.TooltipType;
import net.minecraft.screen.slot.Slot;
import net.minecraft.text.Text;
import net.minecraft.util.Identifier;
import org.lwjgl.glfw.GLFW;

import java.io.Reader;
import java.io.Writer;
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.security.MessageDigest;
import java.time.Duration;
import java.util.ArrayList;
import java.util.HexFormat;
import java.util.List;
import java.util.Locale;
import java.util.UUID;
import java.util.concurrent.CompletableFuture;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

public final class SpookyPriceClient implements ClientModInitializer {
    private static final String DEFAULT_API = "https://spooky-auction-bot-production.up.railway.app";
    private static final Gson GSON = new GsonBuilder().setPrettyPrinting().create();
    private static final Pattern ANARCHY = Pattern.compile("(?i)^an(?:10[1-8]|20[1-9]|30[1-9])(?:\\s.*)?$");
    private static final Pattern PRICE = Pattern.compile(
            "(?iu)(?:цена|стоимость|price|за\\s*штуку|\\$)\\D{0,40}(\\d[\\d\\s.,]*)(?:\\s*)(к|k|тыс|м|m|млн)?"
    );
    private static final HttpClient HTTP = HttpClient.newBuilder().connectTimeout(Duration.ofSeconds(8)).build();

    private KeyBinding scanKey;
    private KeyBinding autoKey;
    private Config config;
    private String currentAnarchy;
    private String lastSignature = "";
    private long lastAutoScanAt = 0L;
    private volatile boolean sending = false;

    @Override
    public void onInitializeClient() {
        config = loadConfig();
        currentAnarchy = config.lastAnarchy;

        var category = KeyBinding.Category.create(Identifier.of("spookyprice", "controls"));
        scanKey = KeyBindingHelper.registerKeyBinding(new KeyBinding(
                "key.spookyprice.scan", InputUtil.Type.KEYSYM, GLFW.GLFW_KEY_F6, category
        ));
        autoKey = KeyBindingHelper.registerKeyBinding(new KeyBinding(
                "key.spookyprice.auto", InputUtil.Type.KEYSYM, GLFW.GLFW_KEY_F7, category
        ));

        ClientSendMessageEvents.COMMAND.register(command -> {
            Matcher matcher = ANARCHY.matcher(command.trim());
            if (matcher.matches()) {
                String first = command.trim().split("\\s+")[0].toLowerCase(Locale.ROOT);
                currentAnarchy = "/" + first;
                config.lastAnarchy = currentAnarchy;
                saveConfig();
                notifyClient("§a[Spooky Price] Анка: " + currentAnarchy);
            }
        });

        ClientTickEvents.END_CLIENT_TICK.register(client -> {
            while (scanKey.wasPressed()) scanCurrentScreen(client, false);

            while (autoKey.wasPressed()) {
                config.autoCollect = !config.autoCollect;
                saveConfig();
                notifyClient(config.autoCollect
                        ? "§a[Spooky Price] Автосбор включён"
                        : "§c[Spooky Price] Автосбор выключен");
            }

            if (config.autoCollect) passiveScanTick(client);
        });
    }

    private void passiveScanTick(MinecraftClient client) {
        if (client.player == null || !(client.currentScreen instanceof HandledScreen<?> handled)) return;
        if (!isAuctionTitle(handled.getTitle().getString())) return;
        if (!validAnarchy(currentAnarchy)) return;

        long now = System.currentTimeMillis();
        if (now - lastAutoScanAt < 1800L) return;

        String signature = screenSignature(client);
        if (signature.equals(lastSignature)) return;

        lastSignature = signature;
        lastAutoScanAt = now;
        scanCurrentScreen(client, true);
    }

    private void scanCurrentScreen(MinecraftClient client, boolean passive) {
        if (sending) {
            if (!passive) notifyClient("§e[Spooky Price] Предыдущая отправка ещё идёт");
            return;
        }

        if (client.player == null || !(client.currentScreen instanceof HandledScreen<?> handled)) {
            if (!passive) notifyClient("§c[Spooky Price] Сначала открой /ah");
            return;
        }

        if (!validAnarchy(currentAnarchy)) {
            if (!passive) notifyClient("§c[Spooky Price] Сначала зайди на анку командой, например /an303");
            return;
        }

        String title = handled.getTitle().getString();
        List<Listing> listings = collectListings(client);

        if (listings.isEmpty()) {
            if (!passive) notifyClient("§e[Spooky Price] В этом окне не нашёл строк с ценой");
            return;
        }

        JsonObject body = new JsonObject();
        body.addProperty("collector", config.collectorId);
        body.addProperty("auction", currentAnarchy);
        body.addProperty("screenTitle", title);
        body.addProperty("clientVersion", "1.0.2");

        JsonArray array = new JsonArray();
        for (Listing listing : listings) {
            JsonObject row = new JsonObject();
            row.addProperty("name", listing.name);
            row.addProperty("rawText", listing.rawText);
            row.addProperty("count", listing.count);
            row.addProperty("slot", listing.slot);
            row.addProperty("fingerprint", listing.fingerprint);
            array.add(row);
        }
        body.add("listings", array);

        sending = true;
        HttpRequest request;
        try {
            request = HttpRequest.newBuilder()
                    .uri(URI.create(config.apiUrl.replaceAll("/+$", "") + "/submit"))
                    .timeout(Duration.ofSeconds(12))
                    .header("Content-Type", "application/json; charset=utf-8")
                    .POST(HttpRequest.BodyPublishers.ofString(GSON.toJson(body), StandardCharsets.UTF_8))
                    .build();
        } catch (Exception ex) {
            sending = false;
            if (!passive) notifyClient("§c[Spooky Price] Неверный адрес API");
            return;
        }

        CompletableFuture<HttpResponse<String>> future = HTTP.sendAsync(
                request, HttpResponse.BodyHandlers.ofString(StandardCharsets.UTF_8)
        );

        future.whenComplete((response, error) -> {
            sending = false;
            if (error != null) {
                notifyClient("§c[Spooky Price] Не удалось отправить цены: " + shortText(error.getMessage()));
                return;
            }

            if (response.statusCode() >= 200 && response.statusCode() < 300) {
                if (!passive) {
                    notifyClient("§a[Spooky Price] Отправлено предметов: " + listings.size() + " • " + currentAnarchy);
                }
            } else {
                notifyClient("§c[Spooky Price] API " + response.statusCode() + ": " + shortText(response.body()));
            }
        });
    }

    private List<Listing> collectListings(MinecraftClient client) {
        List<Listing> result = new ArrayList<>();
        if (client.player == null) return result;

        List<Slot> slots = client.player.currentScreenHandler.slots;
        for (int i = 0; i < slots.size(); i++) {
            ItemStack stack = slots.get(i).getStack();
            if (stack == null || stack.isEmpty()) continue;

            String name = cleanText(stack.getName().getString());
            if (name.isBlank() || looksLikeNavigation(name)) continue;

            String components = String.valueOf(stack.getComponents());

            StringBuilder tooltipBuilder = new StringBuilder();
            try {
                List<Text> tooltip = stack.getTooltip(
                        Item.TooltipContext.create(client.world),
                        client.player,
                        TooltipType.BASIC
                );
                for (Text line : tooltip) {
                    String tooltipLine = cleanText(line.getString());
                    if (!tooltipLine.isBlank()) {
                        if (!tooltipBuilder.isEmpty()) tooltipBuilder.append("\n");
                        tooltipBuilder.append(tooltipLine);
                    }
                }
            } catch (Exception ignored) {
            }

            String tooltipText = tooltipBuilder.toString();
            String raw = tooltipText.isBlank()
                    ? cleanText(name + "\n" + components)
                    : tooltipText;

            if (raw.length() > 6000) raw = raw.substring(0, 6000);

            String fingerprint = sha256(name + "\n" + components + "\n" + stack.getCount());
            result.add(new Listing(name, raw, stack.getCount(), i, fingerprint));
        }
        return result;
    }

    private static Long extractPrice(String raw) {
        Matcher matcher = PRICE.matcher(raw);
        if (!matcher.find()) return null;

        String number = matcher.group(1).replace(" ", "").trim();
        String suffix = matcher.group(2) == null ? "" : matcher.group(2).toLowerCase(Locale.ROOT);

        long multiplier = 1L;
        if (suffix.equals("к") || suffix.equals("k") || suffix.equals("тыс")) multiplier = 1_000L;
        if (suffix.equals("м") || suffix.equals("m") || suffix.equals("млн")) multiplier = 1_000_000L;

        try {
            int commas = countChar(number, ',');
            int dots = countChar(number, '.');
            if (commas + dots > 1 || number.matches(".*[.,]\\d{3}(?:[.,]\\d{3})*$")) {
                number = number.replace(",", "").replace(".", "");
            } else {
                number = number.replace(',', '.');
            }

            double value = Double.parseDouble(number);
            double result = value * multiplier;
            if (!Double.isFinite(result) || result <= 0 || result > 1e15) return null;
            return Math.round(result);
        } catch (NumberFormatException ignored) {
            return null;
        }
    }

    private static int countChar(String s, char c) {
        int n = 0;
        for (int i = 0; i < s.length(); i++) if (s.charAt(i) == c) n++;
        return n;
    }

    private String screenSignature(MinecraftClient client) {
        if (client.player == null) return "";
        StringBuilder out = new StringBuilder();
        for (Slot slot : client.player.currentScreenHandler.slots) {
            ItemStack stack = slot.getStack();
            if (stack == null || stack.isEmpty()) continue;
            out.append(stack.getName().getString())
                    .append('|').append(stack.getCount())
                    .append('|').append(stack.getComponents())
                    .append(';');
        }
        return sha256(out.toString());
    }

    private static boolean isAuctionTitle(String title) {
        String s = cleanText(title).toLowerCase(Locale.ROOT);
        return s.contains("аук")
                || s.contains("auction")
                || s.contains("торг")
                || s.contains("лоты")
                || s.contains("market")
                || s.equals("ah")
                || s.contains("/ah")
                || s.contains("спуки");
    }

    private static boolean looksLikeNavigation(String name) {
        String s = name.toLowerCase(Locale.ROOT);
        return s.contains("назад")
                || s.contains("вперед")
                || s.contains("следующ")
                || s.contains("предыдущ")
                || s.contains("обнов")
                || s.contains("поиск")
                || s.contains("закрыть");
    }

    private static String cleanText(String s) {
        return String.valueOf(s)
                .replaceAll("§[0-9A-FK-ORa-fk-or]", "")
                .replace('\u00A0', ' ')
                .replaceAll("\\s+", " ")
                .trim();
    }

    private static boolean validAnarchy(String a) {
        return a != null && a.matches("(?i)^/an(?:10[1-8]|20[1-9]|30[1-9])$");
    }

    private void notifyClient(String text) {
        MinecraftClient client = MinecraftClient.getInstance();
        client.execute(() -> {
            if (client.inGameHud != null) client.inGameHud.getChatHud().addMessage(Text.literal(text));
        });
    }

    private Config loadConfig() {
        Path path = configPath();
        try {
            Files.createDirectories(path.getParent());
            if (Files.exists(path)) {
                try (Reader reader = Files.newBufferedReader(path, StandardCharsets.UTF_8)) {
                    Config loaded = GSON.fromJson(reader, Config.class);
                    if (loaded != null) {
                        if (loaded.collectorId == null || loaded.collectorId.isBlank()) loaded.collectorId = compactUuid();
                        if (loaded.apiUrl == null || loaded.apiUrl.isBlank()) loaded.apiUrl = DEFAULT_API;
                        return loaded;
                    }
                }
            }
        } catch (Exception ignored) {
        }

        Config fresh = new Config();
        fresh.collectorId = compactUuid();
        fresh.apiUrl = DEFAULT_API;
        fresh.autoCollect = true;
        saveConfig(fresh);
        return fresh;
    }

    private void saveConfig() {
        saveConfig(config);
    }

    private void saveConfig(Config value) {
        Path path = configPath();
        try {
            Files.createDirectories(path.getParent());
            try (Writer writer = Files.newBufferedWriter(path, StandardCharsets.UTF_8)) {
                GSON.toJson(value, writer);
            }
        } catch (Exception ignored) {
        }
    }

    private static Path configPath() {
        return FabricLoader.getInstance().getConfigDir().resolve("spooky-price.json");
    }

    private static String compactUuid() {
        return UUID.randomUUID().toString().replace("-", "");
    }

    private static String sha256(String text) {
        try {
            MessageDigest digest = MessageDigest.getInstance("SHA-256");
            return HexFormat.of().formatHex(digest.digest(text.getBytes(StandardCharsets.UTF_8)));
        } catch (Exception e) {
            return Integer.toHexString(text.hashCode()) + Integer.toHexString(text.length());
        }
    }

    private static String shortText(String text) {
        if (text == null) return "ошибка";
        String clean = cleanText(text);
        return clean.length() > 180 ? clean.substring(0, 180) + "…" : clean;
    }

    private static final class Config {
        String collectorId;
        String apiUrl = DEFAULT_API;
        boolean autoCollect = true;
        String lastAnarchy;
    }

    private record Listing(String name, String rawText, int count, int slot, String fingerprint) {}
}
