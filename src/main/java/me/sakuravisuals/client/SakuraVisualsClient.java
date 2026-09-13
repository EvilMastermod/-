package me.sakuravisuals.client;

import com.mojang.blaze3d.platform.InputConstants;
import net.fabricmc.api.ClientModInitializer;
import net.fabricmc.fabric.api.client.event.lifecycle.v1.ClientTickEvents;
import net.fabricmc.fabric.api.client.keybinding.v1.KeyBindingHelper;
import net.fabricmc.fabric.api.client.rendering.v1.hud.HudElement;
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

    private static final int MENU_BG = 0xE5110B18;
    private static final int PANEL_BG = 0xF3181124;
    private static final int PANEL_BG_ALT = 0xEE130E1E;
    private static final int BORDER = 0xFF2E2022;
    private static final int WHITE = 0xFFFFFFFF;
    private static final int SOFT_TEXT = 0xFFDAB9C7;
    private static final int BLOSSOM_PINK = 0xFFFFD4E3;
    private static final int BLOSSOM_PINK_2 = 0xFFFFB6CF;
    private static final int BLOSSOM_PINK_3 = 0xFFE58AB2;
    private static final int BLOSSOM_PINK_4 = 0xFFD86A9D;

    private static final AccentColor[] ACCENT_COLORS = new AccentColor[]{
            new AccentColor("Розовый", 0xFFFF84BE, 0xFFFFC4E0),
            new AccentColor("Голубой", 0xFF7AC8FF, 0xFFCAE7FF),
            new AccentColor("Фиолетовый", 0xFFB88CFF, 0xFFE1D0FF),
            new AccentColor("Мятный", 0xFF7DE0C1, 0xFFC9F5E8),
            new AccentColor("Белый", 0xFFF3F3F3, 0xFFFFFFFF)
    };

    private static KeyMapping openMenuKey;
    private static double previousGamma = 1.0D;
    private static boolean gammaStored = false;
    private static Double previousDarknessScale = null;
    private static Boolean previousEntityShadows = null;

    @Override
    public void onInitializeClient() {
        CONFIG.load();

        KeyMapping.Category category = KeyMapping.Category.register(
                Identifier.fromNamespaceAndPath(MOD_ID, "main")
        );

        openMenuKey = KeyBindingHelper.registerKeyBinding(new KeyMapping(
                "key.sakuravisuals.open_menu",
                InputConstants.Type.KEYSYM,
                InputConstants.KEY_RSHIFT,
                category
        ));

        ClientTickEvents.END_CLIENT_TICK.register(client -> {
            while (openMenuKey.consumeClick()) {
                client.setScreen(new VisualsScreen(client.screen));
            }
            tickFullBright(client);
        });

        HudElementRegistry.addLast(
                Identifier.fromNamespaceAndPath(MOD_ID, "overlay"),
                createHud()
        );
    }

    private static HudElement createHud() {
        return (graphics, deltaTracker) -> {
            Minecraft mc = Minecraft.getInstance();
            if (mc.player == null || mc.level == null || mc.options.hideGui) return;

            int x = 8;
            int y = 8;
            int line = 11;
            List<String> lines = new ArrayList<>();

            if (CONFIG.watermark) lines.add("Sakura Visuals 1.21.11");
            if (CONFIG.coordinates) {
                lines.add(String.format("XYZ: %.0f / %.0f / %.0f", mc.player.getX(), mc.player.getY(), mc.player.getZ()));
            }
            if (CONFIG.fps) lines.add("FPS: " + mc.getFps());
            if (CONFIG.worldTime) {
                long t = mc.level.getDayTime() % 24000L;
                long hours = ((t / 1000L) + 6L) % 24L;
                long minutes = (t % 1000L) * 60L / 1000L;
                lines.add(String.format("Time: %02d:%02d", hours, minutes));
            }

            int mainBottom = y;
            if (!lines.isEmpty()) {
                int maxWidth = 0;
                for (String s : lines) maxWidth = Math.max(maxWidth, mc.font.width(s));
                if (CONFIG.hudBackground) {
                    graphics.fill(x - 4, y - 4, x + maxWidth + 6, y + lines.size() * line + 3, 0xA1120D18);
                    graphics.fill(x - 4, y - 4, x - 2, y + lines.size() * line + 3, accent());
                }
                for (int i = 0; i < lines.size(); i++) {
                    int color = i == 0 && CONFIG.watermark ? accentLight() : WHITE;
                    graphics.drawString(mc.font, lines.get(i), x, y + i * line, color, true);
                }
                mainBottom = y + lines.size() * line + 10;
            }

            if (CONFIG.playerCard) drawPlayerCard(graphics, mc, x, mainBottom);
            if (CONFIG.crosshair) drawCrosshair(graphics);
            if (CONFIG.sakuraPetals) drawPetals(graphics);
        };
    }

    private static void tickFullBright(Minecraft mc) {
        if (mc == null || mc.options == null) return;

        try {
            OptionInstance<Double> gammaOption = mc.options.gamma();
            OptionInstance<Double> darknessOption = findDoubleOption(mc.options, "darknessEffectScale", "darknessScale");
            OptionInstance<Boolean> entityShadowsOption = findBooleanOption(mc.options, "entityShadows");
            if (CONFIG.fullBright) {
                if (!gammaStored) {
                    previousGamma = gammaOption.get();
                    gammaStored = true;
                }
                gammaOption.set(64.0D);
                if (darknessOption != null) {
                    if (previousDarknessScale == null) previousDarknessScale = darknessOption.get();
                    darknessOption.set(0.0D);
                }
                if (entityShadowsOption != null) {
                    if (previousEntityShadows == null) previousEntityShadows = entityShadowsOption.get();
                    entityShadowsOption.set(false);
                }
            } else {
                if (gammaStored) {
                    gammaOption.set(previousGamma);
                    gammaStored = false;
                }
                if (darknessOption != null && previousDarknessScale != null) {
                    darknessOption.set(previousDarknessScale);
                    previousDarknessScale = null;
                }
                if (entityShadowsOption != null && previousEntityShadows != null) {
                    entityShadowsOption.set(previousEntityShadows);
                    previousEntityShadows = null;
                }
            }
        } catch (Throwable ignored) {
        }
    }

    @SuppressWarnings("unchecked")
    private static OptionInstance<Double> findDoubleOption(Object options, String... methodNames) {
        for (String name : methodNames) {
            try {
                Method m = options.getClass().getMethod(name);
                Object value = m.invoke(options);
                if (value instanceof OptionInstance<?> option) {
                    return (OptionInstance<Double>) option;
                }
            } catch (Throwable ignored) {
            }
        }
        return null;
    }

    @SuppressWarnings("unchecked")
    private static OptionInstance<Boolean> findBooleanOption(Object options, String... methodNames) {
        for (String name : methodNames) {
            try {
                Method m = options.getClass().getMethod(name);
                Object value = m.invoke(options);
                if (value instanceof OptionInstance<?> option) {
                    return (OptionInstance<Boolean>) option;
                }
            } catch (Throwable ignored) {
            }
        }
        return null;
    }

    private static void drawCrosshair(GuiGraphics graphics) {
        int primary = accent();
        int light = accentLight();
        int cx = graphics.guiWidth() / 2 - 1;
        int cy = graphics.guiHeight() / 2 - 1;

        graphics.fill(cx - 4, cy, cx - 1, cy + 1, primary);
        graphics.fill(cx + 2, cy, cx + 5, cy + 1, primary);
        graphics.fill(cx, cy - 4, cx + 1, cy - 1, primary);
        graphics.fill(cx, cy + 2, cx + 1, cy + 5, primary);
        graphics.fill(cx, cy, cx + 1, cy + 1, light);
    }

    private static void drawPlayerCard(GuiGraphics graphics, Minecraft mc, int x, int y) {
        String playerName = mc.player.getName().getString();
        float health = mc.player.getHealth();
        float maxHealth = Math.max(1.0F, mc.player.getMaxHealth());
        float ratio = Math.max(0.0F, Math.min(1.0F, health / maxHealth));

        int width = Math.max(122, mc.font.width(playerName) + 18);
        int height = 35;

        graphics.fill(x - 4, y - 4, x + width + 6, y + height, 0xB1140E18);
        graphics.fill(x - 4, y - 4, x - 2, y + height, accent());
        graphics.fill(x - 2, y - 2, x + width + 4, y + 10, 0x33FFFFFF);
        drawHudBlossom(graphics, x + width - 12, y + 4);

        graphics.drawString(mc.font, playerName, x + 2, y + 2, accentLight(), true);
        graphics.drawString(mc.font, String.format("HP %.1f / %.1f", health, maxHealth), x + 2, y + 13, WHITE, true);

        int barX = x + 2;
        int barY = y + 24;
        int barW = width - 8;
        int fillW = Math.max(0, (int) (barW * ratio));
        graphics.fill(barX, barY, barX + barW, barY + 6, 0xAA241A23);
        graphics.fill(barX, barY, barX + fillW, barY + 6, accent());
        graphics.fill(barX, barY, barX + fillW, barY + 3, accentLight());
    }

    private static void drawHudBlossom(GuiGraphics graphics, int x, int y) {
        graphics.fill(x, y + 1, x + 1, y + 2, 0xFFFFB1CA);
        graphics.fill(x + 1, y, x + 2, y + 1, 0xFFFFB1CA);
        graphics.fill(x + 1, y + 2, x + 2, y + 3, 0xFFFFB1CA);
        graphics.fill(x + 2, y + 1, x + 3, y + 2, 0xFFFFB1CA);
        graphics.fill(x + 1, y + 1, x + 2, y + 2, 0xFFFFE37A);
    }

    private static void drawPetals(GuiGraphics graphics) {
        long now = System.currentTimeMillis();
        int w = Math.max(1, graphics.guiWidth());
        int h = Math.max(1, graphics.guiHeight());
        for (int i = 0; i < 18; i++) {
            long seed = i * 7919L;
            int x = (int) ((seed + now / (18 + (i % 5) * 3)) % (w + 40)) - 20;
            int y = (int) ((seed * 3 + now / (24 + (i % 4) * 4)) % (h + 40)) - 20;
            int size = 1 + (i % 2);
            int color = (i % 3 == 0) ? 0xAAFFF0F7 : 0xAAFF9FCA;
            graphics.fill(x, y, x + size + 1, y + size, color);
            graphics.fill(x + size, y + size, x + size + 2, y + size + 1, color);
        }
    }

    private static int accent() {
        return ACCENT_COLORS[Math.floorMod(CONFIG.accentColorIndex, ACCENT_COLORS.length)].primary;
    }

    private static int accentLight() {
        return ACCENT_COLORS[Math.floorMod(CONFIG.accentColorIndex, ACCENT_COLORS.length)].light;
    }

    private static String accentName() {
        return ACCENT_COLORS[Math.floorMod(CONFIG.accentColorIndex, ACCENT_COLORS.length)].name;
    }

    private static void nextAccentColor() {
        CONFIG.accentColorIndex = (CONFIG.accentColorIndex + 1) % ACCENT_COLORS.length;
        CONFIG.save();
    }

    public static final class VisualsScreen extends Screen {
        private Tab currentTab = Tab.CUSTOM;
        private final Screen parent;

        public VisualsScreen(Screen parent) {
            super(Component.literal("Sakura Visuals"));
            this.parent = parent;
        }

        @Override
        protected void init() {
            rebuildWidgets();
        }

        private void rebuildWidgets() {
            clearWidgets();

            int panelX = this.width / 2 - 210;
            int panelY = this.height / 2 - 135;
            int panelW = 420;
            int leftX = panelX + 18;
            int rightX = panelX + 220;
            int row1Y = panelY + 64;
            int row2Y = panelY + 102;
            int row3Y = panelY + 140;

            addRenderableWidget(new InvisibleButton(panelX + 18, panelY + 20, 122, 26, Component.literal("Кастом"), b -> {
                currentTab = Tab.CUSTOM;
                rebuildWidgets();
            }));
            addRenderableWidget(new InvisibleButton(panelX + 148, panelY + 20, 122, 26, Component.literal("Сакура"), b -> {
                currentTab = Tab.SAKURA;
                rebuildWidgets();
            }));
            addRenderableWidget(new InvisibleButton(panelX + panelW - 108, panelY + 20, 90, 26, Component.literal("Готово"), b -> onClose()));

            if (currentTab == Tab.CUSTOM) {
                addToggleRowButton(leftX, row1Y, () -> CONFIG.crosshair, v -> CONFIG.crosshair = v);
                addToggleRowButton(rightX, row1Y, () -> CONFIG.fullBright, v -> CONFIG.fullBright = v);
                addToggleRowButton(leftX, row2Y, () -> CONFIG.coordinates, v -> CONFIG.coordinates = v);
                addToggleRowButton(rightX, row2Y, () -> CONFIG.fps, v -> CONFIG.fps = v);
                addActionRowButton(leftX, row3Y, b -> {
                    nextAccentColor();
                    rebuildWidgets();
                });
            } else {
                addToggleRowButton(leftX, row1Y, () -> CONFIG.sakuraPetals, v -> CONFIG.sakuraPetals = v);
                addToggleRowButton(rightX, row1Y, () -> CONFIG.watermark, v -> CONFIG.watermark = v);
                addToggleRowButton(leftX, row2Y, () -> CONFIG.hudBackground, v -> CONFIG.hudBackground = v);
                addToggleRowButton(rightX, row2Y, () -> CONFIG.worldTime, v -> CONFIG.worldTime = v);
                addToggleRowButton(leftX, row3Y, () -> CONFIG.playerCard, v -> CONFIG.playerCard = v);
            }
        }

        private void addToggleRowButton(int x, int y, BoolGetter getter, BoolSetter setter) {
            addRenderableWidget(new InvisibleButton(x + 132, y + 7, 52, 20, Component.empty(), b -> {
                boolean next = !getter.get();
                setter.set(next);
                CONFIG.save();
                rebuildWidgets();
            }));
        }

        private void addActionRowButton(int x, int y, Button.OnPress onPress) {
            addRenderableWidget(new InvisibleButton(x + 102, y + 7, 82, 20, Component.empty(), onPress));
        }

        @Override
        public void onClose() {
            CONFIG.save();
            if (this.minecraft != null) this.minecraft.setScreen(parent);
        }

        @Override
        public void render(GuiGraphics graphics, int mouseX, int mouseY, float delta) {
            renderBackground(graphics, mouseX, mouseY, delta);

            int panelX = this.width / 2 - 210;
            int panelY = this.height / 2 - 135;
            int panelW = 420;
            int panelH = 270;
            int leftX = panelX + 18;
            int rightX = panelX + 220;
            int row1Y = panelY + 64;
            int row2Y = panelY + 102;
            int row3Y = panelY + 140;
            int row4Y = panelY + 178;

            graphics.fill(0, 0, this.width, this.height, MENU_BG);
            graphics.fill(panelX, panelY, panelX + panelW, panelY + panelH, PANEL_BG);
            graphics.fill(panelX, panelY, panelX + 10, panelY + panelH, 0xE526123E);
            graphics.fill(panelX, panelY, panelX + panelW, panelY + 2, BLOSSOM_PINK_2);
            graphics.fill(panelX + 12, panelY + 12, panelX + panelW - 12, panelY + 48, PANEL_BG_ALT);

            graphics.drawCenteredString(this.font, this.title, this.width / 2, panelY + 14, BLOSSOM_PINK);
            graphics.drawCenteredString(this.font, Component.literal("Bloom UI • Right Shift"), this.width / 2, panelY + 30, SOFT_TEXT);

            drawSakuraButton(graphics, panelX + 18, panelY + 20, 122, 26, "Кастом", currentTab == Tab.CUSTOM);
            drawSakuraButton(graphics, panelX + 148, panelY + 20, 122, 26, "Сакура", currentTab == Tab.SAKURA);
            drawSakuraButton(graphics, panelX + panelW - 108, panelY + 20, 90, 26, "Готово", false);

            if (currentTab == Tab.CUSTOM) {
                drawToggleRow(graphics, leftX, row1Y, "Прицел", "Кастомный прицел", CONFIG.crosshair);
                drawToggleRow(graphics, rightX, row1Y, "Фул Брайт", "Без темноты и теней", CONFIG.fullBright);
                drawToggleRow(graphics, leftX, row2Y, "Координаты", "Показывать XYZ", CONFIG.coordinates);
                drawToggleRow(graphics, rightX, row2Y, "FPS", "Показывать FPS", CONFIG.fps);
                drawActionRow(graphics, leftX, row3Y, "Цвет", accentName());
                drawPreviewRow(graphics, rightX, row3Y, "Текущий", accent(), accentLight());
                graphics.drawString(this.font, "Выбор цвета меняет прицел и акцент HUD", leftX, row4Y + 12, SOFT_TEXT, true);
            } else {
                drawToggleRow(graphics, leftX, row1Y, "Сакура частицы", "Лепестки на экране", CONFIG.sakuraPetals);
                drawToggleRow(graphics, rightX, row1Y, "Надпись", "Sakura Visuals", CONFIG.watermark);
                drawToggleRow(graphics, leftX, row2Y, "Фон HUD", "Темная подложка", CONFIG.hudBackground);
                drawToggleRow(graphics, rightX, row2Y, "Время мира", "Игровое время", CONFIG.worldTime);
                drawToggleRow(graphics, leftX, row3Y, "Игрок HUD", "Ник и HP слева", CONFIG.playerCard);
                graphics.drawString(this.font, "Игрок HUD сделан в стиле сакуры", leftX, row4Y + 12, SOFT_TEXT, true);
            }

            super.render(graphics, mouseX, mouseY, delta);
        }

        private void drawToggleRow(GuiGraphics graphics, int x, int y, String title, String subtitle, boolean enabled) {
            graphics.fill(x, y, x + 184, y + 30, 0xE1140E18);
            graphics.fill(x, y, x + 184, y + 1, 0x552E2022);
            graphics.drawString(this.font, title, x + 8, y + 7, WHITE, true);
            graphics.drawString(this.font, subtitle, x + 8, y + 18, SOFT_TEXT, true);
            drawSakuraMiniButton(graphics, x + 132, y + 7, 52, 20, enabled ? "ВКЛ" : "ВЫКЛ", enabled);
        }

        private void drawActionRow(GuiGraphics graphics, int x, int y, String title, String value) {
            graphics.fill(x, y, x + 184, y + 30, 0xE1140E18);
            graphics.fill(x, y, x + 184, y + 1, 0x552E2022);
            graphics.drawString(this.font, title, x + 8, y + 7, WHITE, true);
            graphics.drawString(this.font, value, x + 8, y + 18, accentLight(), true);
            drawSakuraMiniButton(graphics, x + 102, y + 7, 82, 20, "Сменить", false);
        }

        private void drawPreviewRow(GuiGraphics graphics, int x, int y, String title, int primary, int light) {
            graphics.fill(x, y, x + 184, y + 30, 0xE1140E18);
            graphics.fill(x, y, x + 184, y + 1, 0x552E2022);
            graphics.drawString(this.font, title, x + 8, y + 7, WHITE, true);
            graphics.drawString(this.font, "Превью", x + 8, y + 18, SOFT_TEXT, true);
            graphics.fill(x + 130, y + 8, x + 175, y + 22, BORDER);
            graphics.fill(x + 131, y + 9, x + 174, y + 21, light);
            graphics.fill(x + 141, y + 14, x + 165, y + 15, primary);
            graphics.fill(x + 153, y + 10, x + 154, y + 20, primary);
        }

        private void drawSakuraButton(GuiGraphics graphics, int x, int y, int width, int height, String text, boolean active) {
            int fill = active ? BLOSSOM_PINK_4 : BLOSSOM_PINK;
            int fill2 = active ? BLOSSOM_PINK_3 : BLOSSOM_PINK_2;
            graphics.fill(x, y, x + width, y + height, BORDER);
            graphics.fill(x + 2, y + 2, x + width - 2, y + height - 2, fill);
            graphics.fill(x + 2, y + 2, x + width - 2, y + height / 2, fill2);
            drawBlossom(graphics, x + 8, y + 8, 1);
            drawBlossom(graphics, x + width - 14, y + height - 12, 1);
            graphics.drawCenteredString(this.font, Component.literal(text), x + width / 2, y + 9, 0xFF281314);
        }

        private void drawSakuraMiniButton(GuiGraphics graphics, int x, int y, int width, int height, String text, boolean pressed) {
            int fill = pressed ? BLOSSOM_PINK_4 : BLOSSOM_PINK_2;
            int fill2 = pressed ? BLOSSOM_PINK_3 : BLOSSOM_PINK;
            graphics.fill(x, y, x + width, y + height, BORDER);
            graphics.fill(x + 2, y + 2, x + width - 2, y + height - 2, fill);
            graphics.fill(x + 2, y + 2, x + width - 2, y + height / 2, fill2);
            drawBlossom(graphics, x + 6, y + 6, 1);
            graphics.drawCenteredString(this.font, Component.literal(text), x + width / 2, y + 6, 0xFF2A1718);
        }

        private void drawBlossom(GuiGraphics graphics, int x, int y, int scale) {
            int s = Math.max(1, scale);
            graphics.fill(x, y + s, x + s, y + 2 * s, 0xFFFFB1CA);
            graphics.fill(x + s, y, x + 2 * s, y + s, 0xFFFFB1CA);
            graphics.fill(x + s, y + 2 * s, x + 2 * s, y + 3 * s, 0xFFFFB1CA);
            graphics.fill(x + 2 * s, y + s, x + 3 * s, y + 2 * s, 0xFFFFB1CA);
            graphics.fill(x + s, y + s, x + 2 * s, y + 2 * s, 0xFFFFE37A);
        }
    }

    private static final class InvisibleButton extends Button {
        private InvisibleButton(int x, int y, int width, int height, Component message, OnPress onPress) {
            super(x, y, width, height, message, onPress, DEFAULT_NARRATION);
        }

        @Override
        protected void renderWidget(GuiGraphics guiGraphics, int mouseX, int mouseY, float partialTick) {
        }
    }

    private enum Tab {
        CUSTOM,
        SAKURA
    }

    private record AccentColor(String name, int primary, int light) {
    }

    @FunctionalInterface
    private interface BoolGetter { boolean get(); }

    @FunctionalInterface
    private interface BoolSetter { void set(boolean value); }
}
