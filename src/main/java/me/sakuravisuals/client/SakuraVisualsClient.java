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
    private static final int SOFT = 0xFFD9BAC7;
    private static final int BG = 0xE5120C19;
    private static final int PANEL = 0xF2191125;
    private static final int CARD = 0xEE100B17;
    private static final int BORDER = 0xFF34272B;
    private static final int PINK = 0xFFFFD5E3;
    private static final int PINK_TOP = 0xFFFFE7ED;
    private static final int PINK_ON = 0xFFE681AB;
    private static final int PINK_ON_TOP = 0xFFF29BBD;

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
            while (menuKey.consumeClick()) client.setScreen(new VisualsScreen(client.screen, Tab.CUSTOM));
            tickFullBright(client);
        });

        HudElementRegistry.addLast(Identifier.fromNamespaceAndPath(MOD_ID, "overlay"), (graphics, deltaTracker) -> renderHud(graphics));
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

        int bottom = y;
        if (!lines.isEmpty()) {
            int max = 0;
            for (String s : lines) max = Math.max(max, mc.font.width(s));
            if (CONFIG.hudBackground) {
                graphics.fill(x - 4, y - 4, x + max + 6, y + lines.size() * line + 3, 0xA5120D18);
                graphics.fill(x - 4, y - 4, x - 2, y + lines.size() * line + 3, accent());
            }
            for (int i = 0; i < lines.size(); i++)
                graphics.drawString(mc.font, lines.get(i), x, y + i * line, i == 0 ? accentLight() : WHITE, true);
            bottom = y + lines.size() * line + 10;
        }

        if (CONFIG.playerCard) drawPlayerCard(graphics, mc, x, bottom);
        if (CONFIG.crosshair) drawCrosshair(graphics);
        if (CONFIG.sakuraPetals) drawPetals(graphics);
    }

    private static void drawPlayerCard(GuiGraphics g, Minecraft mc, int x, int y) {
        String name = mc.player.getName().getString();
        float hp = mc.player.getHealth();
        float maxHp = Math.max(1.0F, mc.player.getMaxHealth());
        float ratio = Math.max(0.0F, Math.min(1.0F, hp / maxHp));
        int w = Math.max(126, mc.font.width(name) + 22);

        g.fill(x - 4, y - 4, x + w + 6, y + 35, 0xB8140E18);
        g.fill(x - 4, y - 4, x - 2, y + 35, accent());
        g.fill(x - 2, y - 2, x + w + 4, y + 9, 0x22FFFFFF);
        blossom(g, x + w - 12, y + 3);
        g.drawString(mc.font, name, x + 2, y + 2, accentLight(), true);
        g.drawString(mc.font, String.format("HP %.1f / %.1f", hp, maxHp), x + 2, y + 13, WHITE, true);

        int barW = w - 8;
        int fillW = (int) (barW * ratio);
        g.fill(x + 2, y + 24, x + 2 + barW, y + 30, 0xAA241A23);
        g.fill(x + 2, y + 24, x + 2 + fillW, y + 30, accent());
        g.fill(x + 2, y + 24, x + 2 + fillW, y + 27, accentLight());
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
        for (int i = 0; i < 18; i++) {
            long seed = i * 7919L;
            int x = (int) ((seed + now / (18 + (i % 5) * 3)) % (w + 40)) - 20;
            int y = (int) ((seed * 3 + now / (24 + (i % 4) * 4)) % (h + 40)) - 20;
            int s = 1 + (i % 2);
            int c = i % 3 == 0 ? 0xAAFFF0F7 : 0xAAFF9FCA;
            g.fill(x, y, x + s + 1, y + s, c);
            g.fill(x + s, y + s, x + s + 2, y + s + 1, c);
        }
    }

    private static int idx() { return Math.floorMod(CONFIG.accentColorIndex, COLORS.length); }
    private static int accent() { return COLORS[idx()]; }
    private static int accentLight() { return LIGHT[idx()]; }
    private static String accentName() { return COLOR_NAMES[idx()]; }
    private static void nextAccent() { CONFIG.accentColorIndex = (idx() + 1) % COLORS.length; CONFIG.save(); }

    private enum Tab { CUSTOM, SAKURA }

    public static final class VisualsScreen extends Screen {
        private final Screen parent;
        private final Tab tab;

        public VisualsScreen(Screen parent, Tab tab) {
            super(Component.literal("Sakura Visuals"));
            this.parent = parent;
            this.tab = tab;
        }

        @Override
        protected void init() {
            int center = width / 2, top = height / 2 - 120;
            int left = center - 175, right = center + 8;

            addInvisible(center - 175, top + 30, 165, 28, () -> minecraft.setScreen(new VisualsScreen(parent, Tab.CUSTOM)));
            addInvisible(center + 10, top + 30, 165, 28, () -> minecraft.setScreen(new VisualsScreen(parent, Tab.SAKURA)));
            addInvisible(center - 70, top + 207, 140, 26, this::onClose);

            int r1 = top + 78, r2 = top + 118, r3 = top + 158;
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
                addToggle(left, r2, () -> CONFIG.worldTime = !CONFIG.worldTime);
                addToggle(right, r2, () -> CONFIG.hudBackground = !CONFIG.hudBackground);
                addToggle(left, r3, () -> CONFIG.playerCard = !CONFIG.playerCard);
            }
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
            int center = width / 2, top = height / 2 - 120;
            int left = center - 175, right = center + 8;
            int r1 = top + 78, r2 = top + 118, r3 = top + 158;

            g.fill(0, 0, width, height, BG);
            g.fill(center - 200, top, center + 200, top + 245, PANEL);
            g.fill(center - 200, top, center + 200, top + 2, PINK_ON_TOP);
            g.fill(center - 200, top, center - 196, top + 245, 0xFFE28AAF);

            g.drawCenteredString(font, title, center, top + 8, 0xFFFFD7E4);
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
                card(g, left, r2, "Время мира", "Игровые часы", CONFIG.worldTime);
                card(g, right, r2, "Фон HUD", "Темная подложка", CONFIG.hudBackground);
                card(g, left, r3, "Игрок HUD", "Ник и HP слева", CONFIG.playerCard);
            }

            drawBigButton(g, center - 70, top + 207, 140, 26, "Готово", false);
            g.drawCenteredString(font, Component.literal("Bloom UI • Right Shift"), center, top + 232, SOFT);
            super.render(g, mouseX, mouseY, delta);
        }

        private void card(GuiGraphics g, int x, int y, String a, String b, boolean on) {
            g.fill(x, y, x + 167, y + 32, CARD);
            g.fill(x, y, x + 167, y + 1, 0x55433237);
            g.drawString(font, a, x + 8, y + 7, WHITE, true);
            g.drawString(font, b, x + 8, y + 19, SOFT, true);
            miniButton(g, x + 119, y + 6, 42, 20, on ? "ВКЛ" : "ВЫКЛ", on);
        }

        private void colorCard(GuiGraphics g, int x, int y) {
            g.fill(x, y, x + 167, y + 32, CARD);
            g.drawString(font, "Цвет", x + 8, y + 7, WHITE, true);
            g.drawString(font, accentName(), x + 8, y + 19, accentLight(), true);
            g.fill(x + 112, y + 7, x + 159, y + 25, BORDER);
            g.fill(x + 114, y + 9, x + 157, y + 23, accentLight());
            g.fill(x + 124, y + 15, x + 147, y + 16, accent());
            g.fill(x + 135, y + 11, x + 136, y + 21, accent());
        }

        private void drawBigButton(GuiGraphics g, int x, int y, int w, int h, String text, boolean selected) {
            int base = selected ? PINK_ON : PINK;
            int top = selected ? PINK_ON_TOP : PINK_TOP;
            g.fill(x, y, x + w, y + h, BORDER);
            g.fill(x + 2, y + 2, x + w - 2, y + h - 2, base);
            g.fill(x + 2, y + 2, x + w - 2, y + h / 2, top);
            blossom(g, x + 7, y + 7);
            blossom(g, x + w - 13, y + h - 11);
            g.drawCenteredString(font, Component.literal(text), x + w / 2, y + 9, 0xFF281314);
        }

        private void miniButton(GuiGraphics g, int x, int y, int w, int h, String text, boolean pressed) {
            int base = pressed ? PINK_ON : PINK;
            int top = pressed ? PINK_ON_TOP : PINK_TOP;
            g.fill(x, y, x + w, y + h, BORDER);
            g.fill(x + 2, y + 2, x + w - 2, y + h - 2, base);
            g.fill(x + 2, y + 2, x + w - 2, y + h / 2, top);
            blossom(g, x + 5, y + 5);
            g.drawCenteredString(font, Component.literal(text), x + w / 2, y + 6, 0xFF291719);
        }
    }

    private static void blossom(GuiGraphics g, int x, int y) {
        g.fill(x, y + 1, x + 1, y + 2, 0xFFFFB1CA);
        g.fill(x + 1, y, x + 2, y + 1, 0xFFFFB1CA);
        g.fill(x + 1, y + 2, x + 2, y + 3, 0xFFFFB1CA);
        g.fill(x + 2, y + 1, x + 3, y + 2, 0xFFFFB1CA);
        g.fill(x + 1, y + 1, x + 2, y + 2, 0xFFFFE37A);
    }
}
