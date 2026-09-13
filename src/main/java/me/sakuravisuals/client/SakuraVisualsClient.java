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
    private static final int SOFT = 0xFFE7E7EE;
    private static final int BG = 0xE5120C19;
    private static final int PANEL = 0xF2191125;
    private static final int CARD = 0xEE100B17;
    private static final int BORDER = 0xFF34272B;

    private static final String[] COLOR_NAMES = {"Розовый", "Голубой", "Фиолетовый", "Мятный", "Белый"};
    private static final int[] COLORS = {0xFFFF82BA, 0xFF72C7FF, 0xFFB38CFF, 0xFF72DEBE, 0xFFF4F4F4};
    private static final int[] LIGHT = {0xFFFFD9EA, 0xFFDDF3FF, 0xFFEDE3FF, 0xFFDCF9F0, 0xFFFFFFFF};

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
            while (menuKey.consumeClick()) {
                client.setScreen(new VisualsScreen(client.screen, Tab.CUSTOM, System.nanoTime()));
            }
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

    static List<String> hudLines(Minecraft mc) {
        List<String> lines = new ArrayList<>();
        if (mc == null || mc.player == null || mc.level == null) return lines;
        if (CONFIG.watermark) lines.add("Sakura Visuals 1.21.11");
        if (CONFIG.coordinates) lines.add(String.format("XYZ: %.0f / %.0f / %.0f", mc.player.getX(), mc.player.getY(), mc.player.getZ()));
        if (CONFIG.fps) lines.add("FPS: " + mc.getFps());
        if (CONFIG.worldTime) {
            long t = mc.level.getDayTime() % 24000L;
            lines.add(String.format("Time: %02d:%02d", ((t / 1000L) + 6L) % 24L, (t % 1000L) * 60L / 1000L));
        }
        return lines;
    }

    static int hudInfoBaseWidth(Minecraft mc) {
        int max = 96;
        if (mc != null) {
            for (String line : hudLines(mc)) max = Math.max(max, mc.font.width(line));
        }
        return max + 14;
    }

    static int hudInfoBaseHeight(Minecraft mc) {
        int count = Math.max(1, hudLines(mc).size());
        return count * 11 + 9;
    }

    private static void renderHud(GuiGraphics graphics) {
        Minecraft mc = Minecraft.getInstance();
        if (mc.player == null || mc.level == null || mc.options.hideGui) return;

        List<String> lines = hudLines(mc);
        if (!lines.isEmpty()) {
            float scale = clampScale(CONFIG.hudInfoScale);
            var matrices = graphics.pose();
            matrices.pushMatrix();
            matrices.translate(CONFIG.hudInfoX, CONFIG.hudInfoY);
            matrices.scale(scale, scale);

            int width = hudInfoBaseWidth(mc);
            int height = hudInfoBaseHeight(mc);
            if (CONFIG.hudBackground) {
                graphics.fill(0, 0, width, height, 0xA5120D18);
                graphics.fill(0, 0, 3, height, accent());
                graphics.fill(3, 0, width, 2, withAlpha(accentLight(), 0x55));
            }
            for (int i = 0; i < lines.size(); i++) {
                graphics.drawString(mc.font, lines.get(i), 7, 5 + i * 11,
                        i == 0 ? accentLight() : WHITE, true);
            }
            matrices.popMatrix();
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
        int c1 = withAlpha(brighten(accentLight(), 1.08F), 0xC8);
        int c2 = withAlpha(0xFFFFFFFF, 0xD0);
        for (int i = 0; i < 18; i++) {
            long seed = i * 7919L;
            int x = (int) ((seed + now / (18 + (i % 5) * 3)) % (w + 40)) - 20;
            int y = (int) ((seed * 3 + now / (24 + (i % 4) * 4)) % (h + 40)) - 20;
            int s = 1 + (i % 2);
            int c = i % 4 == 0 ? c2 : c1;
            g.fill(x, y, x + s + 1, y + s, c);
            g.fill(x + s, y + s, x + s + 2, y + s + 1, c);
        }
    }

    private static int idx() { return Math.floorMod(CONFIG.accentColorIndex, COLORS.length); }
    public static int accent() { return COLORS[idx()]; }
    public static int accentLight() { return LIGHT[idx()]; }
    public static int accentVeryLight() { return brighten(LIGHT[idx()], 1.10F); }
    public static String accentName() { return COLOR_NAMES[idx()]; }
    private static void nextAccent() { CONFIG.accentColorIndex = (idx() + 1) % COLORS.length; CONFIG.save(); }
    private static int withAlpha(int color, int alpha) { return (alpha << 24) | (color & 0x00FFFFFF); }

    static float clampScale(int percent) {
        return Math.max(0.55F, Math.min(1.90F, percent / 100.0F));
    }

    private static int brighten(int color, float factor) {
        int r = Math.min(255, (int) (((color >> 16) & 0xFF) * factor));
        int g = Math.min(255, (int) (((color >> 8) & 0xFF) * factor));
        int b = Math.min(255, (int) ((color & 0xFF) * factor));
        return 0xFF000000 | (r << 16) | (g << 8) | b;
    }

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

        private MenuLayout layout() {
            int size = Math.floorMod(CONFIG.menuSize, 3);
            int cardW = size == 0 ? 148 : size == 2 ? 188 : 167;
            int cardH = size == 0 ? 29 : size == 2 ? 36 : 32;
            int gapX = size == 0 ? 12 : size == 2 ? 20 : 16;
            int gapY = size == 0 ? 7 : size == 2 ? 11 : 8;
            int panelW = cardW * 2 + gapX + 50;
            int header = size == 0 ? 68 : size == 2 ? 82 : 74;
            int bottom = size == 0 ? 63 : size == 2 ? 78 : 70;
            int panelH = header + (cardH + gapY) * 4 + bottom;
            int panelX = (width - panelW) / 2;
            int panelY = (height - panelH) / 2;
            return new MenuLayout(panelX, panelY, panelW, panelH, cardW, cardH, gapX, gapY, header);
        }

        @Override
        protected void init() {
            MenuLayout l = layout();
            int left = l.panelX + 20;
            int right = left + l.cardW + l.gapX;
            int tabY = l.panelY + 30;
            int tabH = Math.max(24, l.cardH - 3);
            int row1 = l.panelY + l.header;
            int row2 = row1 + l.cardH + l.gapY;
            int row3 = row2 + l.cardH + l.gapY;
            int row4 = row3 + l.cardH + l.gapY;

            addInvisible(left, tabY, l.cardW, tabH, () ->
                    minecraft.setScreen(new VisualsScreen(parent, Tab.CUSTOM, openedAt)));
            addInvisible(right, tabY, l.cardW, tabH, () ->
                    minecraft.setScreen(new VisualsScreen(parent, Tab.SAKURA, openedAt)));

            if (tab == Tab.CUSTOM) {
                addToggle(left, row1, l, () -> CONFIG.crosshair = !CONFIG.crosshair);
                addToggle(right, row1, l, () -> CONFIG.fullBright = !CONFIG.fullBright);
                addToggle(left, row2, l, () -> CONFIG.coordinates = !CONFIG.coordinates);
                addToggle(right, row2, l, () -> CONFIG.fps = !CONFIG.fps);
                addInvisible(left, row3, l.cardW, l.cardH, SakuraVisualsClient::nextAccent);
                addToggle(right, row3, l, () -> CONFIG.hudBackground = !CONFIG.hudBackground);
                addInvisible(left, row4, l.cardW, l.cardH, () -> {
                    CONFIG.menuSize = (Math.floorMod(CONFIG.menuSize, 3) + 1) % 3;
                    CONFIG.save();
                    minecraft.setScreen(new VisualsScreen(parent, tab, System.nanoTime()));
                });
                addInvisible(right, row4, l.cardW, l.cardH, () -> minecraft.setScreen(new HudEditorScreen(this)));
            } else {
                addToggle(left, row1, l, () -> CONFIG.sakuraPetals = !CONFIG.sakuraPetals);
                addToggle(right, row1, l, () -> CONFIG.watermark = !CONFIG.watermark);
                addToggle(left, row2, l, () -> CONFIG.playerCard = !CONFIG.playerCard);
                addToggle(right, row2, l, () -> CONFIG.playerTrail = !CONFIG.playerTrail);
                addInvisible(left, row3, l.cardW, l.cardH, () -> {
                    CONFIG.trailMode = (CONFIG.trailMode + 1) % 2;
                    CONFIG.save();
                });
                addToggle(right, row3, l, () -> CONFIG.worldTime = !CONFIG.worldTime);
                addToggle(left, row4, l, () -> CONFIG.hudBackground = !CONFIG.hudBackground);
            }

            int doneW = Math.min(150, l.cardW);
            addInvisible(width / 2 - doneW / 2, l.panelY + l.panelH - 42, doneW, 26, this::onClose);
        }

        private void addToggle(int x, int y, MenuLayout l, Runnable action) {
            addInvisible(x, y, l.cardW, l.cardH, () -> { action.run(); CONFIG.save(); });
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
            MenuLayout base = layout();
            float progress = Math.min(1.0F, (System.nanoTime() - openedAt) / 220_000_000.0F);
            float eased = 1.0F - (1.0F - progress) * (1.0F - progress);
            int slide = (int) ((1.0F - eased) * 28.0F);
            MenuLayout l = base.offsetY(slide);

            int left = l.panelX + 20;
            int right = left + l.cardW + l.gapX;
            int tabY = l.panelY + 30;
            int tabH = Math.max(24, l.cardH - 3);
            int row1 = l.panelY + l.header;
            int row2 = row1 + l.cardH + l.gapY;
            int row3 = row2 + l.cardH + l.gapY;
            int row4 = row3 + l.cardH + l.gapY;

            g.fill(0, 0, width, height, BG);
            g.fill(l.panelX, l.panelY, l.panelX + l.panelW, l.panelY + l.panelH, PANEL);
            g.fill(l.panelX, l.panelY, l.panelX + l.panelW, l.panelY + 2, accentLight());
            g.fill(l.panelX, l.panelY, l.panelX + 4, l.panelY + l.panelH, accent());

            g.drawCenteredString(font, title, width / 2, l.panelY + 8, WHITE);
            drawBigButton(g, left, tabY, l.cardW, tabH, "Кастом", tab == Tab.CUSTOM);
            drawBigButton(g, right, tabY, l.cardW, tabH, "Сакура", tab == Tab.SAKURA);

            if (tab == Tab.CUSTOM) {
                card(g, left, row1, l, "Прицел", "Кастомный цветной", CONFIG.crosshair);
                card(g, right, row1, l, "Фул Брайт", "Без темноты и теней", CONFIG.fullBright);
                card(g, left, row2, l, "Координаты", "Показывать XYZ", CONFIG.coordinates);
                card(g, right, row2, l, "FPS", "Показывать FPS", CONFIG.fps);
                colorCard(g, left, row3, l);
                card(g, right, row3, l, "Фон HUD", "Подложка у HUD", CONFIG.hudBackground);
                actionCard(g, left, row4, l, "Размер меню", menuSizeName());
                actionCard(g, right, row4, l, "Редактор HUD", "Перетащить / изменить");
            } else {
                card(g, left, row1, l, "Лепестки", "Светлая сакура", CONFIG.sakuraPetals);
                card(g, right, row1, l, "Watermark", "Sakura Visuals", CONFIG.watermark);
                card(g, left, row2, l, "Игрок HUD", "Скин, ник и HP", CONFIG.playerCard);
                card(g, right, row2, l, "След игрока", "Включить эффект", CONFIG.playerTrail);
                actionCard(g, left, row3, l, "Тип следа", CONFIG.trailMode == 0 ? "Лепестки" : "Линия");
                card(g, right, row3, l, "Время мира", "Игровые часы", CONFIG.worldTime);
                card(g, left, row4, l, "Фон HUD", "Темная подложка", CONFIG.hudBackground);
            }

            int doneW = Math.min(150, l.cardW);
            drawBigButton(g, width / 2 - doneW / 2, l.panelY + l.panelH - 42, doneW, 26, "Готово", false);
            g.drawCenteredString(font, Component.literal("Right Shift - открыть меню"), width / 2,
                    l.panelY + l.panelH - 14, SOFT);
            super.render(g, mouseX, mouseY, delta);
        }

        private String menuSizeName() {
            return switch (Math.floorMod(CONFIG.menuSize, 3)) {
                case 0 -> "Маленькое";
                case 2 -> "Большое";
                default -> "Среднее";
            };
        }

        private void card(GuiGraphics g, int x, int y, MenuLayout l, String a, String b, boolean on) {
            g.fill(x, y, x + l.cardW, y + l.cardH, CARD);
            g.fill(x, y, x + l.cardW, y + 1, withAlpha(accent(), 0x66));
            g.drawString(font, a, x + 8, y + 6, WHITE, true);
            g.drawString(font, b, x + 8, y + Math.max(17, l.cardH - 13), WHITE, false);
            int bw = 44;
            miniButton(g, x + l.cardW - bw - 6, y + (l.cardH - 20) / 2, bw, 20, on ? "ВКЛ" : "ВЫКЛ", on);
        }

        private void actionCard(GuiGraphics g, int x, int y, MenuLayout l, String title, String value) {
            g.fill(x, y, x + l.cardW, y + l.cardH, CARD);
            g.fill(x, y, x + l.cardW, y + 1, withAlpha(accent(), 0x66));
            g.drawString(font, title, x + 8, y + 6, WHITE, true);
            g.drawString(font, value, x + 8, y + Math.max(17, l.cardH - 13), WHITE, false);
            miniButton(g, x + l.cardW - 30, y + (l.cardH - 20) / 2, 24, 20, ">", false);
        }

        private void colorCard(GuiGraphics g, int x, int y, MenuLayout l) {
            g.fill(x, y, x + l.cardW, y + l.cardH, CARD);
            g.fill(x, y, x + l.cardW, y + 1, withAlpha(accent(), 0x66));
            g.drawString(font, "Цвет", x + 8, y + 6, WHITE, true);
            g.drawString(font, accentName(), x + 8, y + Math.max(17, l.cardH - 13), WHITE, false);
            int px = x + l.cardW - 53;
            int py = y + (l.cardH - 20) / 2;
            g.fill(px, py, px + 47, py + 20, BORDER);
            g.fill(px + 2, py + 2, px + 45, py + 18, accentLight());
            g.fill(px + 12, py + 9, px + 35, py + 10, accent());
            g.fill(px + 23, py + 5, px + 24, py + 15, accent());
        }

        private void drawBigButton(GuiGraphics g, int x, int y, int w, int h, String text, boolean selected) {
            int base = selected ? darker(accent()) : accent();
            int topColor = selected ? darker(accentLight()) : accentLight();
            g.fill(x, y, x + w, y + h, BORDER);
            g.fill(x + 2, y + 2, x + w - 2, y + h - 2, base);
            g.fill(x + 2, y + 2, x + w - 2, y + h / 2, topColor);
            blossom(g, x + 7, y + 7);
            blossom(g, x + w - 13, y + h - 11);
            g.drawCenteredString(font, Component.literal(text), x + w / 2, y + Math.max(6, h / 2 - 4), WHITE);
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

    private record MenuLayout(int panelX, int panelY, int panelW, int panelH,
                              int cardW, int cardH, int gapX, int gapY, int header) {
        MenuLayout offsetY(int delta) {
            return new MenuLayout(panelX, panelY + delta, panelW, panelH, cardW, cardH, gapX, gapY, header);
        }
    }

    static void blossom(GuiGraphics g, int x, int y) {
        int petal = accentLight();
        int center = WHITE;
        g.fill(x, y + 1, x + 1, y + 2, petal);
        g.fill(x + 1, y, x + 2, y + 1, petal);
        g.fill(x + 1, y + 2, x + 2, y + 3, petal);
        g.fill(x + 2, y + 1, x + 3, y + 2, petal);
        g.fill(x + 1, y + 1, x + 2, y + 2, center);
    }
}
