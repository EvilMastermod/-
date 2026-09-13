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

    private static KeyMapping openMenuKey;

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
        int cx = graphics.guiWidth() / 2;
        int cy = graphics.guiHeight() / 2;
        graphics.fill(cx - 5, cy, cx - 1, cy + 1, PINK);
        graphics.fill(cx + 2, cy, cx + 6, cy + 1, PINK);
        graphics.fill(cx, cy - 5, cx + 1, cy - 1, PINK);
        graphics.fill(cx, cy + 2, cx + 1, cy + 6, PINK);
        graphics.fill(cx, cy, cx + 1, cy + 1, WHITE);
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

    public static final class VisualsScreen extends Screen {
        private final Screen parent;

        public VisualsScreen(Screen parent) {
            super(Component.literal("Sakura Visuals"));
            this.parent = parent;
        }

        @Override
        protected void init() {
            int buttonWidth = 150;
            int gap = 8;
            int left = this.width / 2 - buttonWidth - gap / 2;
            int right = this.width / 2 + gap / 2;
            int y = this.height / 2 - 78;

            addToggle(left, y, buttonWidth, "Watermark", () -> CONFIG.watermark, v -> CONFIG.watermark = v);
            addToggle(right, y, buttonWidth, "Координаты", () -> CONFIG.coordinates, v -> CONFIG.coordinates = v);
            y += 26;
            addToggle(left, y, buttonWidth, "FPS", () -> CONFIG.fps, v -> CONFIG.fps = v);
            addToggle(right, y, buttonWidth, "Время мира", () -> CONFIG.worldTime, v -> CONFIG.worldTime = v);
            y += 26;
            addToggle(left, y, buttonWidth, "Розовый прицел", () -> CONFIG.crosshair, v -> CONFIG.crosshair = v);
            addToggle(right, y, buttonWidth, "Лепестки сакуры", () -> CONFIG.sakuraPetals, v -> CONFIG.sakuraPetals = v);
            y += 26;
            addToggle(left, y, buttonWidth, "Фон HUD", () -> CONFIG.hudBackground, v -> CONFIG.hudBackground = v);

            this.addRenderableWidget(Button.builder(Component.literal("Готово"), b -> onClose())
                    .bounds(right, y, buttonWidth, 20).build());
        }

        private void addToggle(int x, int y, int width, String label, BoolGetter getter, BoolSetter setter) {
            Button button = Button.builder(toggleText(label, getter.get()), b -> {
                boolean next = !getter.get();
                setter.set(next);
                CONFIG.save();
                b.setMessage(toggleText(label, next));
            }).bounds(x, y, width, 20).build();
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
            graphics.fill(0, 0, this.width, this.height, 0xD0100A16);
            graphics.fill(this.width / 2 - 175, this.height / 2 - 115,
                    this.width / 2 + 175, this.height / 2 + 80, 0xD91A1022);
            graphics.fill(this.width / 2 - 175, this.height / 2 - 115,
                    this.width / 2 + 175, this.height / 2 - 111, PINK);
            graphics.drawCenteredString(this.font, this.title, this.width / 2, this.height / 2 - 101, LIGHT_PINK);
            graphics.drawCenteredString(this.font, "Right Shift — открыть меню", this.width / 2, this.height / 2 - 88, 0xFFB9AFC0);
            super.render(graphics, mouseX, mouseY, delta);
        }
    }

    @FunctionalInterface
    private interface BoolGetter { boolean get(); }

    @FunctionalInterface
    private interface BoolSetter { void set(boolean value); }
}
