package me.sakuravisuals.client;

import com.mojang.blaze3d.platform.InputConstants;
import net.fabricmc.api.ClientModInitializer;
import net.fabricmc.fabric.api.client.event.lifecycle.v1.ClientTickEvents;
import net.fabricmc.fabric.api.client.keybinding.v1.KeyBindingHelper;
import net.fabricmc.fabric.api.client.rendering.v1.hud.HudElement;
import net.fabricmc.fabric.api.client.rendering.v1.hud.HudElementRegistry;
import net.minecraft.client.KeyMapping;
import net.minecraft.client.Minecraft;
import net.minecraft.client.gui.GuiGraphics;
import net.minecraft.client.gui.components.Button;
import net.minecraft.client.gui.screens.Screen;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.Identifier;

import java.util.ArrayList;
import java.util.List;

public final class SakuraVisualsClient implements ClientModInitializer {
    public static final String MOD_ID = "sakuravisuals";
    public static final VisualConfig CONFIG = new VisualConfig();

    private static final int WHITE = 0xFFFFFFFF;
    private static final int MENU_BG = 0xE5120C19;
    private static final int PANEL = 0xF21A1125;
    private static final int CARD = 0xEE100B17;
    private static final int BORDER = 0xFF34272B;
    private static final int SOFT_TEXT = 0xFFDDBBC8;
    private static final int PINK_NORMAL = 0xFFFFCEDC;
    private static final int PINK_HOVER = 0xFFFFA8C7;
    private static final int PINK_PRESSED = 0xFFE184A9;

    private static final String[] COLOR_NAMES = {
            "Розовый", "Голубой", "Фиолетовый", "Мятный", "Белый"
    };
    private static final int[] COLORS = {
            0xFFFF82BA, 0xFF72C7FF, 0xFFB38CFF, 0xFF72DEBE, 0xFFF4F4F4
    };
    private static final int[] LIGHT_COLORS = {
            0xFFFFC7E0, 0xFFCCE9FF, 0xFFE3D3FF, 0xFFC9F4E7, 0xFFFFFFFF
    };

    private static KeyMapping openMenuKey;
    private static boolean fullBrightApplied;
    private static double oldGamma = 0.5D;
    private static double oldDarknessScale = 1.0D;

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
                client.setScreen(new VisualsScreen(client.screen, Tab.CUSTOM));
            }
            tickFullBright(client);
        });

        HudElementRegistry.addLast(
                Identifier.fromNamespaceAndPath(MOD_ID, "overlay"),
                createHud()
        );
    }

    private static void tickFullBright(Minecraft mc) {
        if (mc == null || mc.options == null) return;

        if (CONFIG.fullBright) {
            if (!fullBrightApplied) {
                oldGamma = mc.options.gamma().get();
                oldDarknessScale = mc.options.darknessEffectScale().get();
                fullBrightApplied = true;
            }
            mc.options.gamma().set(1.0D);
            mc.options.darknessEffectScale().set(0.0D);
        } else if (fullBrightApplied) {
            mc.options.gamma().set(oldGamma);
            mc.options.darknessEffectScale().set(oldDarknessScale);
            fullBrightApplied = false;
        }
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

            if (!lines.isEmpty()) {
                int maxWidth = 0;
                for (String s : lines) maxWidth = Math.max(maxWidth, mc.font.width(s));
                if (CONFIG.hudBackground) {
                    graphics.fill(x - 4, y - 4, x + maxWidth + 6, y + lines.size() * line + 3, 0xA5120D18);
                    graphics.fill(x - 4, y - 4, x - 2, y + lines.size() * line + 3, accent());
                }
                for (int i = 0; i < lines.size(); i++) {
                    int color = i == 0 && CONFIG.watermark ? accentLight() : WHITE;
                    graphics.drawString(mc.font, lines.get(i), x, y + i * line, color, true);
                }
            }

            if (CONFIG.crosshair) drawCrosshair(graphics);
            if (CONFIG.sakuraPetals) drawPetals(graphics);
        };
    }

    private static void drawCrosshair(GuiGraphics graphics) {
        int cx = graphics.guiWidth() / 2 - 1;
        int cy = graphics.guiHeight() / 2 - 1;
        int primary = accent();
        int light = accentLight();

        graphics.fill(cx - 4, cy, cx - 1, cy + 1, primary);
        graphics.fill(cx + 2, cy, cx + 5, cy + 1, primary);
        graphics.fill(cx, cy - 4, cx + 1, cy - 1, primary);
        graphics.fill(cx, cy + 2, cx + 1, cy + 5, primary);
        graphics.fill(cx, cy, cx + 1, cy + 1, light);
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

    private static int colorIndex() {
        return Math.floorMod(CONFIG.accentColorIndex, COLORS.length);
    }

    private static int accent() {
        return COLORS[colorIndex()];
    }

    private static int accentLight() {
        return LIGHT_COLORS[colorIndex()];
    }

    private static String accentName() {
        return COLOR_NAMES[colorIndex()];
    }

    private static void nextAccent() {
        CONFIG.accentColorIndex = (colorIndex() + 1) % COLORS.length;
        CONFIG.save();
    }

    private enum Tab {
        CUSTOM,
        SAKURA
    }

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
            int center = this.width / 2;
            int top = this.height / 2 - 120;
            int left = center - 175;
            int right = center + 8;

            addInvisibleButton(center - 175, top + 30, 165, 28, () ->
                    this.minecraft.setScreen(new VisualsScreen(parent, Tab.CUSTOM)));
            addInvisibleButton(center + 10, top + 30, 165, 28, () ->
                    this.minecraft.setScreen(new VisualsScreen(parent, Tab.SAKURA)));

            int row1 = top + 78;
            int row2 = top + 118;
            int row3 = top + 158;

            if (tab == Tab.CUSTOM) {
                addToggleHitbox(left, row1, () -> CONFIG.crosshair = !CONFIG.crosshair);
                addToggleHitbox(right, row1, () -> CONFIG.fullBright = !CONFIG.fullBright);
                addToggleHitbox(left, row2, () -> CONFIG.coordinates = !CONFIG.coordinates);
                addToggleHitbox(right, row2, () -> CONFIG.fps = !CONFIG.fps);
                addInvisibleButton(left, row3, 167, 32, SakuraVisualsClient::nextAccent);
                addToggleHitbox(right, row3, () -> CONFIG.hudBackground = !CONFIG.hudBackground);
            } else {
                addToggleHitbox(left, row1, () -> CONFIG.sakuraPetals = !CONFIG.sakuraPetals);
                addToggleHitbox(right, row1, () -> CONFIG.watermark = !CONFIG.watermark);
                addToggleHitbox(left, row2, () -> CONFIG.worldTime = !CONFIG.worldTime);
                addToggleHitbox(right, row2, () -> CONFIG.hudBackground = !CONFIG.hudBackground);
            }

            addInvisibleButton(center - 70, top + 207, 140, 26, this::onClose);
        }

        private void addToggleHitbox(int x, int y, Runnable action) {
            addInvisibleButton(x, y, 167, 32, () -> {
                action.run();
                CONFIG.save();
            });
        }

        private void addInvisibleButton(int x, int y, int width, int height, Runnable action) {
            Button button = Button.builder(Component.literal(""), b -> action.run())
                    .bounds(x, y, width, height)
                    .build();
            button.setAlpha(0.0F);
            this.addRenderableWidget(button);
        }

        @Override
        public void onClose() {
            CONFIG.save();
            if (this.minecraft != null) this.minecraft.setScreen(parent);
        }

        @Override
        public void render(GuiGraphics graphics, int mouseX, int mouseY, float delta) {
            int center = this.width / 2;
            int top = this.height / 2 - 120;
            int left = center - 175;
            int right = center + 8;
            int row1 = top + 78;
            int row2 = top + 118;
            int row3 = top + 158;

            graphics.fill(0, 0, this.width, this.height, MENU_BG);
            graphics.fill(center - 200, top, center + 200, top + 245, PANEL);
            graphics.fill(center - 200, top, center + 200, top + 2, PINK_HOVER);
            graphics.fill(center - 200, top, center - 196, top + 245, 0xFFE28AAF);

            graphics.drawCenteredString(this.font, this.title, center, top + 9, 0xFFFFD5E4);

            drawSakuraButton(graphics, center - 175, top + 30, 165, 28, "Кастом", tab == Tab.CUSTOM);
            drawSakuraButton(graphics, center + 10, top + 30, 165, 28, "Сакура", tab == Tab.SAKURA);

            if (tab == Tab.CUSTOM) {
                drawToggleCard(graphics, left, row1, "Прицел", "Кастомный цветной", CONFIG.crosshair);
                drawToggleCard(graphics, right, row1, "Фул Брайт", "Макс. яркость + без Darkness", CONFIG.fullBright);
                drawToggleCard(graphics, left, row2, "Координаты", "Показывать XYZ", CONFIG.coordinates);
                drawToggleCard(graphics, right, row2, "FPS", "Показывать FPS", CONFIG.fps);
                drawColorCard(graphics, left, row3);
                drawToggleCard(graphics, right, row3, "Фон HUD", "Подложка у HUD", CONFIG.hudBackground);
            } else {
                drawToggleCard(graphics, left, row1, "Лепестки", "Сакура на экране", CONFIG.sakuraPetals);
                drawToggleCard(graphics, right, row1, "Watermark", "Sakura Visuals", CONFIG.watermark);
                drawToggleCard(graphics, left, row2, "Время мира", "Игровые часы", CONFIG.worldTime);
                drawToggleCard(graphics, right, row2, "Фон HUD", "Темная подложка", CONFIG.hudBackground);
            }

            drawSakuraButton(graphics, center - 70, top + 207, 140, 26, "Готово", false);
            graphics.drawCenteredString(this.font, "Right Shift - открыть меню", center, top + 232, SOFT_TEXT);

            super.render(graphics, mouseX, mouseY, delta);
        }

        private void drawToggleCard(GuiGraphics graphics, int x, int y, String title, String subtitle, boolean enabled) {
            graphics.fill(x, y, x + 167, y + 32, CARD);
            graphics.fill(x, y, x + 167, y + 1, 0x55433237);
            graphics.drawString(this.font, title, x + 8, y + 7, WHITE, false);
            graphics.drawString(this.font, subtitle, x + 8, y + 19, SOFT_TEXT, false);
            drawMiniSakuraButton(graphics, x + 119, y + 6, 42, 20, enabled ? "ВКЛ" : "ВЫКЛ", enabled);
        }

        private void drawColorCard(GuiGraphics graphics, int x, int y) {
            graphics.fill(x, y, x + 167, y + 32, CARD);
            graphics.drawString(this.font, "Цвет", x + 8, y + 7, WHITE, false);
            graphics.drawString(this.font, accentName(), x + 8, y + 19, accentLight(), false);
            graphics.fill(x + 112, y + 7, x + 159, y + 25, BORDER);
            graphics.fill(x + 114, y + 9, x + 157, y + 23, accentLight());
            graphics.fill(x + 124, y + 15, x + 147, y + 16, accent());
            graphics.fill(x + 135, y + 11, x + 136, y + 21, accent());
        }

        private void drawSakuraButton(GuiGraphics graphics, int x, int y, int width, int height, String text, boolean selected) {
            int base = selected ? PINK_HOVER : PINK_NORMAL;
            int topColor = selected ? 0xFFFFBCD2 : 0xFFFFE0E8;
            graphics.fill(x, y, x + width, y + height, BORDER);
            graphics.fill(x + 2, y + 2, x + width - 2, y + height - 2, base);
            graphics.fill(x + 2, y + 2, x + width - 2, y + height / 2, topColor);
            drawBlossom(graphics, x + 8, y + 7);
            drawBlossom(graphics, x + width - 13, y + height - 12);
            graphics.drawCenteredString(this.font, Component.literal(text), x + width / 2, y + 10, 0xFF2D171B);
        }

        private void drawMiniSakuraButton(GuiGraphics graphics, int x, int y, int width, int height, String text, boolean enabled) {
            int base = enabled ? PINK_PRESSED : PINK_NORMAL;
            graphics.fill(x, y, x + width, y + height, BORDER);
            graphics.fill(x + 2, y + 2, x + width - 2, y + height - 2, base);
            graphics.fill(x + 2, y + 2, x + width - 2, y + height / 2, enabled ? 0xFFECA0BE : 0xFFFFE1E9);
            drawBlossom(graphics, x + 5, y + 6);
            graphics.drawCenteredString(this.font, Component.literal(text), x + width / 2 + 4, y + 6, 0xFF2D171B);
        }

        private void drawBlossom(GuiGraphics graphics, int x, int y) {
            graphics.fill(x, y + 1, x + 1, y + 2, 0xFFFF9FBE);
            graphics.fill(x + 1, y, x + 2, y + 1, 0xFFFFB0CA);
            graphics.fill(x + 1, y + 2, x + 2, y + 3, 0xFFFFB0CA);
            graphics.fill(x + 2, y + 1, x + 3, y + 2, 0xFFFF9FBE);
            graphics.fill(x + 1, y + 1, x + 2, y + 2, 0xFFFFE071);
        }
    }
}
