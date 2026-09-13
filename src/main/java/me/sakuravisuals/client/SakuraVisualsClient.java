package me.sakuravisuals.client;

import com.mojang.blaze3d.platform.InputConstants;
import net.fabricmc.api.ClientModInitializer;
import net.fabricmc.fabric.api.client.event.lifecycle.v1.ClientTickEvents;
import net.fabricmc.fabric.api.client.keybinding.v1.KeyBindingHelper;
import net.fabricmc.fabric.api.client.rendering.v1.hud.HudElementRegistry;
import net.minecraft.client.KeyMapping;
import net.minecraft.client.Minecraft;
import net.minecraft.client.OptionInstance;
import net.minecraft.client.gui.GuiGraphics;
import net.minecraft.client.gui.components.Button;
import net.minecraft.client.gui.screens.Screen;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.Identifier;

import java.lang.reflect.Method;
import java.util.ArrayList;
import java.util.List;

public final class SakuraVisualsClient implements ClientModInitializer {
    public static final String MOD_ID = "sakuravisuals";
    public static final VisualConfig CONFIG = new VisualConfig();

    private static final int WHITE = 0xFFFFFFFF;
    private static final int SOFT = 0xFFD9D9E2;
    private static final int BG = 0xE5120C19;
    private static final int PANEL = 0xF2191125;
    private static final int CARD = 0xEE100B17;
    private static final int BORDER = 0xFF34272B;

    private static final String[] COLOR_NAMES = {"Розовый", "Голубой", "Фиолетовый", "Мятный", "Белый"};
    private static final int[] COLORS = {0xFFFF82BA, 0xFF72C7FF, 0xFFB38CFF, 0xFF72DEBE, 0xFFF4F4F4};
    private static final int[] LIGHT = {0xFFFFC7E0, 0xFFCCE9FF, 0xFFE3D3FF, 0xFFC9F4E7, 0xFFFFFFFF};

    private static KeyMapping menuKey;
    private static boolean fullBrightApplied;
    private static double oldGamma = 0.5D;
    private static double oldDarkness = 1.0D;
    private static Boolean oldEntityShadows;

    @Override
    public void onInitializeClient() {
        CONFIG.load();
        KeyMapping.Category category = KeyMapping.Category.register(Identifier.fromNamespaceAndPath(MOD_ID, "main"));
        menuKey = KeyBindingHelper.registerKeyBinding(new KeyMapping(
                "key.sakuravisuals.open_menu", InputConstants.Type.KEYSYM, InputConstants.KEY_RSHIFT, category));

        ClientTickEvents.END_CLIENT_TICK.register(client -> {
            while (menuKey.consumeClick()) client.setScreen(new VisualsScreen(client.screen, Tab.CUSTOM, System.nanoTime()));
            tickFullBright(client);
        });

        HudElementRegistry.addLast(Identifier.fromNamespaceAndPath(MOD_ID, "overlay"),
                (graphics, deltaTracker) -> renderHud(graphics));
    }

    private static void tickFullBright(Minecraft mc) {
        if (mc == null || mc.options == null) return;
        if (CONFIG.fullBright) {
            if (!fullBrightApplied) {
                oldGamma = mc.options.gamma().get();
                oldDarkness = mc.options.darknessEffectScale().get();
                oldEntityShadows = readBooleanOption(mc.options, "entityShadows");
                fullBrightApplied = true;
            }
            mc.options.gamma().set(1.0D);
            mc.options.darknessEffectScale().set(0.0D);
            writeBooleanOption(mc.options, "entityShadows", false);
        } else if (fullBrightApplied) {
            mc.options.gamma().set(oldGamma);
            mc.options.darknessEffectScale().set(oldDarkness);
            if (oldEntityShadows != null) writeBooleanOption(mc.options, "entityShadows", oldEntityShadows);
            oldEntityShadows = null;
            fullBrightApplied = false;
        }
    }

    @SuppressWarnings("unchecked")
    private static Boolean readBooleanOption(Object options, String methodName) {
        try {
            Method m = options.getClass().getMethod(methodName);
            Object value = m.invoke(options);
            if (value instanceof OptionInstance<?> option) return ((OptionInstance<Boolean>) option).get();
        } catch (Throwable ignored) {}
        return null;
    }

    @SuppressWarnings("unchecked")
    private static void writeBooleanOption(Object options, String methodName, boolean value) {
        try {
            Method m = options.getClass().getMethod(methodName);
            Object result = m.invoke(options);
            if (result instanceof OptionInstance<?> option) ((OptionInstance<Boolean>) option).set(value);
        } catch (Throwable ignored) {}
    }

    private static void renderHud(GuiGraphics graphics) {
        Minecraft mc = Minecraft.getInstance();
        if (mc.player == null || mc.level == null || mc.options.hideGui) return;

        int x = 8, y = 8, line = 11;
        List<String> lines = new ArrayList<>();
        if (CONFIG.watermark) lines.add("Sakura Visuals 1.21.11");
        if (CONFIG.coordinates) lines.add(String.format("XYZ: %.0f / %.0f / %.0f", mc.player.getX(), mc.player.getY(), mc.player.getZ()));
        if (CONFIG.fps) lines.add("FPS: " + mc.getFps());
        if (CONFIG.worldTime) {
            long t = mc.level.getDayTime() % 24000L;
            lines.add(String.format("Time: %02d:%02d", ((t / 1000L) + 6L) % 24L, (t % 1000L) * 60L / 1000L));
        }

        if (!lines.isEmpty()) {
            int max = 0;
            for (String s : lines) max = Math.max(max, mc.font.width(s));
            if (CONFIG.hudBackground) {
                graphics.fill(x - 4, y - 4, x + max + 6, y + lines.size() * line + 3, 0xA5120D18);
                graphics.fill(x - 4, y - 4, x - 2, y + lines.size() * line + 3, accent());
            }
            for (int i = 0; i < lines.size(); i++)
                graphics.drawString(mc.font, lines.get(i), x, y + i * line, i == 0 ? accentLight() : WHITE, true);
        }

        if (CONFIG.crosshair) drawCrosshair(graphics);
        if (CONFIG.sakuraPetals) drawPetals(graphics);
    }

    private static void drawCrosshair(GuiGraphics g) {
        int cx = g.guiWidth() / 2 - 1, cy = g.guiHeight() / 2 - 1;
        g.fill(cx - 4, cy, cx - 1, cy + 1, accent());
        g.fill(cx + 2, cy, cx + 5, cy + 1, accent());
        g.fill(cx, cy - 4, cx + 1, cy - 1, accent());
        g.fill(cx, cy + 2, cx + 1, cy + 5, accent());
        g.fill(cx, cy, cx + 1, cy + 1, accentLight());
    }

    private static void drawPetals(GuiGraphics g) {
        long now = System.currentTimeMillis();
        int w = Math.max(1, g.guiWidth()), h = Math.max(1, g.guiHeight());
        int c1 = withAlpha(accent(), 0xAA);
        int c2 = withAlpha(accentLight(), 0xAA);
        for (int i = 0; i < 18; i++) {
            long seed = i * 7919L;
            int x = (int) ((seed + now / (18 + (i % 5) * 3)) % (w + 40)) - 20;
            int y = (int) ((seed * 3 + now / (24 + (i % 4) * 4)) % (h + 40)) - 20;
            int s = 1 + (i % 2);
            int c = i % 3 == 0 ? c2 : c1;
            g.fill(x, y, x + s + 1, y + s, c);
            g.fill(x + s, y + s, x + s + 2, y + s + 1, c);
        }
    }

    private static int idx() { return Math.floorMod(CONFIG.accentColorIndex, COLORS.length); }
    public static int accent() { return COLORS[idx()]; }
    public static int accentLight() { return LIGHT[idx()]; }
    public static String accentName() { return COLOR_NAMES[idx()]; }
    private static void nextAccent() { CONFIG.accentColorIndex = (idx() + 1) % COLORS.length; CONFIG.save(); }
    private static int withAlpha(int color, int alpha) { return (alpha << 24) | (color & 0x00FFFFFF); }

    private static int darker(int color) {
        int r = (color >> 16) & 0xFF;
        int g = (color >> 8) & 0xFF;
        int b = color & 0xFF;
        r = (int) (r * 0.72F);
        g = (int) (g * 0.72F);
        b = (int) (b * 0.72F);
        return 0xFF000000 | (r << 16) | (g << 8) | b;
    }

    private enum Tab { CUSTOM, SAKURA }

    public static final class VisualsScreen extends Screen {
        private final Screen parent;
        private final Tab tab;
        private final long openedAt;

        public VisualsScreen(Screen parent, Tab tab, long openedAt) {
            super(Component.literal("Sakura Visuals"));
            this.parent = parent;
            this.tab = tab;
            this.openedAt = openedAt;
        }

        @Override
        protected void init() {
            int center = width / 2, top = height / 2 - 138;
            int left = center - 175, right = center + 8;

            addInvisible(center - 175, top + 30, 165, 28, () ->
                    minecraft.setScreen(new VisualsScreen(parent, Tab.CUSTOM, openedAt)));
            addInvisible(center + 10, top + 30, 165, 28, () ->
                    minecraft.setScreen(new VisualsScreen(parent, Tab.SAKURA, openedAt)));

            int r1 = top + 78, r2 = top + 118, r3 = top + 158, r4 = top + 198;
            if (tab == Tab.CUSTOM) {
                addToggle(left, r1, () -> CONFIG.crosshair = !CONFIG.crosshair);
                addToggle(right, r1, () -> CONFIG.fullBright = !CONFIG.fullBright);
                addToggle(left, r2, () -> CONFIG.coordinates = !CONFIG.coordinates);
                addToggle(right, r2, () -> CONFIG.fps = !CONFIG.fps);
                addInvisible(left, r3, 167, 32, SakuraVisualsClient::nextAccent);
                addToggle(right, r3, () -> CONFIG.hudBackground = !CONFIG.hudBackground);
            } else {
                addToggle(left, r1, () -> CONFIG.sakuraPetals = !CONFIG.sakuraPetals);
                addToggle(right, r1, () -> CONFIG.watermark = !CONFIG.watermark);
                addToggle(left, r2, () -> CONFIG.playerCard = !CONFIG.playerCard);
                addToggle(right, r2, () -> CONFIG.playerTrail = !CONFIG.playerTrail);
                addInvisible(left, r3, 167, 32, () -> { CONFIG.trailMode = (CONFIG.trailMode + 1) % 2; CONFIG.save(); });
                addInvisible(right, r3, 167, 32, () -> { CONFIG.trailSize = (CONFIG.trailSize + 1) % 3; CONFIG.save(); });
                addToggle(left, r4, () -> CONFIG.worldTime = !CONFIG.worldTime);
                addToggle(right, r4, () -> CONFIG.hudBackground = !CONFIG.hudBackground);
            }

            addInvisible(center - 70, top + 247, 140, 26, this::onClose);
        }

        private void addToggle(int x, int y, Runnable action) {
            addInvisible(x, y, 167, 32, () -> { action.run(); CONFIG.save(); });
        }

        private void addInvisible(int x, int y, int w, int h, Runnable action) {
            Button b = Button.builder(Component.empty(), button -> action.run()).bounds(x, y, w, h).build();
            b.setAlpha(0.0F);
            addRenderableWidget(b);
        }

        @Override
        public void onClose() {
            CONFIG.save();
            if (minecraft != null) minecraft.setScreen(parent);
        }

        @Override
        public void render(GuiGraphics g, int mouseX, int mouseY, float delta) {
            float progress = Math.min(1.0F, (System.nanoTime() - openedAt) / 220_000_000.0F);
            float eased = 1.0F - (1.0F - progress) * (1.0F - progress);
            int slide = (int) ((1.0F - eased) * 28.0F);

            int center = width / 2, top = height / 2 - 138 + slide;
            int left = center - 175, right = center + 8;
            int r1 = top + 78, r2 = top + 118, r3 = top + 158, r4 = top + 198;

            g.fill(0, 0, width, height, BG);
            g.fill(center - 200, top, center + 200, top + 285, PANEL);
            g.fill(center - 200, top, center + 200, top + 2, accentLight());
            g.fill(center - 200, top, center - 196, top + 285, accent());

            g.drawCenteredString(font, title, center, top + 8, WHITE);
            drawBigButton(g, center - 175, top + 30, 165, 28, "Кастом", tab == Tab.CUSTOM);
            drawBigButton(g, center + 10, top + 30, 165, 28, "Сакура", tab == Tab.SAKURA);

            if (tab == Tab.CUSTOM) {
                card(g, left, r1, "Прицел", "Кастомный цветной", CONFIG.crosshair);
                card(g, right, r1, "Фул Брайт", "Без темноты и теней", CONFIG.fullBright);
                card(g, left, r2, "Координаты", "Показывать XYZ", CONFIG.coordinates);
                card(g, right, r2, "FPS", "Показывать FPS", CONFIG.fps);
                colorCard(g, left, r3);
                card(g, right, r3, "Фон HUD", "Подложка у HUD", CONFIG.hudBackground);
            } else {
                card(g, left, r1, "Лепестки", "Сакура на экране", CONFIG.sakuraPetals);
                card(g, right, r1, "Watermark", "Sakura Visuals", CONFIG.watermark);
                card(g, left, r2, "Игрок HUD", "Скин, ник и HP", CONFIG.playerCard);
                card(g, right, r2, "След игрока", "Включить эффект", CONFIG.playerTrail);
                actionCard(g, left, r3, "Тип следа", CONFIG.trailMode == 0 ? "Лепестки" : "Линия");
                actionCard(g, right, r3, "Размер следа", trailSizeName());
                card(g, left, r4, "Время мира", "Игровые часы", CONFIG.worldTime);
                card(g, right, r4, "Фон HUD", "Темная подложка", CONFIG.hudBackground);
            }

            drawBigButton(g, center - 70, top + 247, 140, 26, "Готово", false);
            g.drawCenteredString(font, Component.literal("Right Shift - открыть меню"), center, top + 272, SOFT);
            super.render(g, mouseX, mouseY, delta);
        }

        private String trailSizeName() {
            return switch (Math.floorMod(CONFIG.trailSize, 3)) {
                case 0 -> "Маленький";
                case 2 -> "Большой";
                default -> "Средний";
            };
        }

        private void card(GuiGraphics g, int x, int y, String a, String b, boolean on) {
            g.fill(x, y, x + 167, y + 32, CARD);
            g.fill(x, y, x + 167, y + 1, withAlpha(accent(), 0x55));
            g.drawString(font, a, x + 8, y + 7, WHITE, true);
            g.drawString(font, b, x + 8, y + 19, WHITE, false);
            miniButton(g, x + 119, y + 6, 42, 20, on ? "ВКЛ" : "ВЫКЛ", on);
        }

        private void actionCard(GuiGraphics g, int x, int y, String title, String value) {
            g.fill(x, y, x + 167, y + 32, CARD);
            g.fill(x, y, x + 167, y + 1, withAlpha(accent(), 0x55));
            g.drawString(font, title, x + 8, y + 7, WHITE, true);
            g.drawString(font, value, x + 8, y + 19, WHITE, false);
            miniButton(g, x + 119, y + 6, 42, 20, ">", false);
        }

        private void colorCard(GuiGraphics g, int x, int y) {
            g.fill(x, y, x + 167, y + 32, CARD);
            g.fill(x, y, x + 167, y + 1, withAlpha(accent(), 0x55));
            g.drawString(font, "Цвет", x + 8, y + 7, WHITE, true);
            g.drawString(font, accentName(), x + 8, y + 19, WHITE, false);
            g.fill(x + 112, y + 7, x + 159, y + 25, BORDER);
            g.fill(x + 114, y + 9, x + 157, y + 23, accentLight());
            g.fill(x + 124, y + 15, x + 147, y + 16, accent());
            g.fill(x + 135, y + 11, x + 136, y + 21, accent());
        }

        private void drawBigButton(GuiGraphics g, int x, int y, int w, int h, String text, boolean selected) {
            int base = selected ? darker(accent()) : accent();
            int topColor = selected ? darker(accentLight()) : accentLight();
            g.fill(x, y, x + w, y + h, BORDER);
            g.fill(x + 2, y + 2, x + w - 2, y + h - 2, base);
            g.fill(x + 2, y + 2, x + w - 2, y + h / 2, topColor);
            blossom(g, x + 7, y + 7);
            blossom(g, x + w - 13, y + h - 11);
            g.drawCenteredString(font, Component.literal(text), x + w / 2, y + 9, WHITE);
        }

        private void miniButton(GuiGraphics g, int x, int y, int w, int h, String text, boolean pressed) {
            int base = pressed ? darker(accent()) : accent();
            int topColor = pressed ? darker(accentLight()) : accentLight();
            g.fill(x, y, x + w, y + h, BORDER);
            g.fill(x + 2, y + 2, x + w - 2, y + h - 2, base);
            g.fill(x + 2, y + 2, x + w - 2, y + h / 2, topColor);
            blossom(g, x + 5, y + 5);
            g.drawCenteredString(font, Component.literal(text), x + w / 2, y + 6, WHITE);
        }
    }

    private static void blossom(GuiGraphics g, int x, int y) {
        int petal = accentLight();
        int center = WHITE;
        g.fill(x, y + 1, x + 1, y + 2, petal);
        g.fill(x + 1, y, x + 2, y + 1, petal);
        g.fill(x + 1, y + 2, x + 2, y + 3, petal);
        g.fill(x + 2, y + 1, x + 3, y + 2, petal);
        g.fill(x + 1, y + 1, x + 2, y + 2, center);
    }
}
