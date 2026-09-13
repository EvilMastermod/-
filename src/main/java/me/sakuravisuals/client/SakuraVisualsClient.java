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

    private static final int PINK = 0xFFFF8FC7;
    private static final int LIGHT_PINK = 0xFFFFC4DF;
    private static final int WHITE = 0xFFFFFFFF;
    private static final int BOX = 0xA0140E1B;
    private static final int MENU_BG = 0xE4100A16;
    private static final int PANEL = 0xE91A1026;
    private static final int TAB_IDLE = 0xFF281A45;
    private static final int TAB_ACTIVE = 0xFF8A2D67;

    private static KeyMapping openMenuKey;
    private static boolean fullBrightApplied;
    private static double oldGamma = 0.5D;

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
                fullBrightApplied = true;
            }
            if (mc.options.gamma().get() < 1.0D) {
                mc.options.gamma().set(1.0D);
            }
        } else if (fullBrightApplied) {
            mc.options.gamma().set(oldGamma);
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
                    graphics.fill(x - 4, y - 4, x + maxWidth + 5, y + lines.size() * line + 2, BOX);
                    graphics.fill(x - 4, y - 4, x - 2, y + lines.size() * line + 2, PINK);
                }
                for (int i = 0; i < lines.size(); i++) {
                    int color = i == 0 && CONFIG.watermark ? LIGHT_PINK : WHITE;
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
        graphics.fill(cx - 4, cy, cx - 1, cy + 1, PINK);
        graphics.fill(cx + 2, cy, cx + 5, cy + 1, PINK);
        graphics.fill(cx, cy - 4, cx + 1, cy - 1, PINK);
        graphics.fill(cx, cy + 2, cx + 1, cy + 5, PINK);
        graphics.fill(cx, cy, cx + 1, cy + 1, LIGHT_PINK);
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

    private enum Tab {
        CUSTOM("Кастом"),
        SAKURA("Сакура");

        final String title;
        Tab(String title) { this.title = title; }
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
            int top = this.height / 2 - 110;

            this.addRenderableWidget(Button.builder(Component.literal("Кастом"), b ->
                    this.minecraft.setScreen(new VisualsScreen(parent, Tab.CUSTOM)))
                    .bounds(center - 155, top + 24, 145, 22).build());
            this.addRenderableWidget(Button.builder(Component.literal("Сакура"), b ->
                    this.minecraft.setScreen(new VisualsScreen(parent, Tab.SAKURA)))
                    .bounds(center + 10, top + 24, 145, 22).build());

            int left = center - 155;
            int right = center + 10;
            int y = top + 64;

            if (tab == Tab.CUSTOM) {
                addToggle(left, y, 145, "Прицел", () -> CONFIG.crosshair, v -> CONFIG.crosshair = v);
                addToggle(right, y, 145, "FullBright", () -> CONFIG.fullBright, v -> CONFIG.fullBright = v);
                y += 28;
                addToggle(left, y, 145, "Координаты", () -> CONFIG.coordinates, v -> CONFIG.coordinates = v);
                addToggle(right, y, 145, "FPS", () -> CONFIG.fps, v -> CONFIG.fps = v);
                y += 28;
                addToggle(left, y, 145, "Время мира", () -> CONFIG.worldTime, v -> CONFIG.worldTime = v);
                addToggle(right, y, 145, "Фон HUD", () -> CONFIG.hudBackground, v -> CONFIG.hudBackground = v);
            } else {
                addToggle(left, y, 145, "Лепестки сакуры", () -> CONFIG.sakuraPetals, v -> CONFIG.sakuraPetals = v);
                addToggle(right, y, 145, "Watermark", () -> CONFIG.watermark, v -> CONFIG.watermark = v);
            }

            this.addRenderableWidget(Button.builder(Component.literal("Готово"), b -> onClose())
                    .bounds(center - 70, top + 178, 140, 22).build());
        }

        private void addToggle(int x, int y, int width, String label, BoolGetter getter, BoolSetter setter) {
            Button button = Button.builder(toggleText(label, getter.get()), b -> {
                boolean next = !getter.get();
                setter.set(next);
                CONFIG.save();
                b.setMessage(toggleText(label, next));
            }).bounds(x, y, width, 22).build();
            this.addRenderableWidget(button);
        }

        private Component toggleText(String label, boolean enabled) {
            return Component.literal(label + ": " + (enabled ? "ВКЛ" : "ВЫКЛ"));
        }

        @Override
        public void onClose() {
            CONFIG.save();
            if (this.minecraft != null) this.minecraft.setScreen(parent);
        }

        @Override
        public void render(GuiGraphics graphics, int mouseX, int mouseY, float delta) {
            int center = this.width / 2;
            int top = this.height / 2 - 110;
            graphics.fill(0, 0, this.width, this.height, MENU_BG);
            graphics.fill(center - 180, top, center + 180, top + 215, PANEL);
            graphics.fill(center - 180, top, center - 176, top + 215, PINK);
            graphics.fill(center - 180, top, center + 180, top + 2, LIGHT_PINK);

            int customColor = tab == Tab.CUSTOM ? TAB_ACTIVE : TAB_IDLE;
            int sakuraColor = tab == Tab.SAKURA ? TAB_ACTIVE : TAB_IDLE;
            graphics.fill(center - 155, top + 24, center - 10, top + 46, customColor);
            graphics.fill(center + 10, top + 24, center + 155, top + 46, sakuraColor);

            graphics.drawCenteredString(this.font, this.title, center, top + 8, LIGHT_PINK);
            graphics.drawCenteredString(this.font, "Right Shift — открыть меню", center, top + 50, 0xFFB9AFC0);
            super.render(graphics, mouseX, mouseY, delta);
        }
    }

    @FunctionalInterface
    private interface BoolGetter { boolean get(); }

    @FunctionalInterface
    private interface BoolSetter { void set(boolean value); }
}
