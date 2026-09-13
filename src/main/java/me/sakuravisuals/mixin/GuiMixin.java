package me.sakuravisuals.mixin;

import me.sakuravisuals.client.SakuraVisualsClient;
import net.minecraft.client.DeltaTracker;
import net.minecraft.client.Minecraft;
import net.minecraft.client.gui.Gui;
import net.minecraft.client.gui.GuiGraphics;
import net.minecraft.world.entity.player.Player;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;

@Mixin(Gui.class)
public abstract class GuiMixin {
    @Inject(method = "renderCrosshair", at = @At("HEAD"), cancellable = true)
    private void sakuraVisuals$hideVanillaCrosshair(GuiGraphics graphics, DeltaTracker deltaTracker, CallbackInfo ci) {
        if (SakuraVisualsClient.CONFIG.crosshair) {
            ci.cancel();
        }
    }

    @Inject(method = "renderItemHotbar", at = @At("TAIL"))
    private void sakuraVisuals$decorateHotbar(GuiGraphics graphics, DeltaTracker deltaTracker, CallbackInfo ci) {
        Minecraft mc = Minecraft.getInstance();
        if (mc.player == null || mc.options.hideGui) return;

        int accent = sakuraVisuals$uiAccent();
        int light = sakuraVisuals$uiLight();
        int x = graphics.guiWidth() / 2 - 91;
        int y = graphics.guiHeight() - 22;

        // Outer accent frame. This keeps the vanilla item rendering intact.
        graphics.fill(x - 2, y - 2, x + 184, y - 1, accent);
        graphics.fill(x - 2, y + 22, x + 184, y + 23, accent);
        graphics.fill(x - 2, y - 2, x - 1, y + 23, accent);
        graphics.fill(x + 183, y - 2, x + 184, y + 23, accent);

        int selected = Math.floorMod(mc.player.getInventory().getSelectedSlot(), 9);
        int sx = x + 1 + selected * 20;
        graphics.fill(sx, y, sx + 20, y + 1, light);
        graphics.fill(sx, y + 20, sx + 20, y + 21, light);
        graphics.fill(sx, y, sx + 1, y + 21, light);
        graphics.fill(sx + 19, y, sx + 20, y + 21, light);

        if (SakuraVisualsClient.CONFIG.uiStyle == 1) {
            sakuraVisuals$blossom(graphics, x - 5, y - 5, light);
            sakuraVisuals$blossom(graphics, x + 180, y - 5, light);
            sakuraVisuals$blossom(graphics, x - 5, y + 20, light);
            sakuraVisuals$blossom(graphics, x + 180, y + 20, light);
        }
    }

    @Inject(method = "renderHearts", at = @At("HEAD"), cancellable = true)
    private void sakuraVisuals$renderColoredHearts(
            GuiGraphics graphics,
            Player player,
            int x,
            int y,
            int lines,
            int regeneratingHeartIndex,
            float maxHealth,
            int lastHealth,
            int health,
            int absorption,
            boolean blinking,
            CallbackInfo ci
    ) {
        int accent = sakuraVisuals$uiAccent();
        int light = sakuraVisuals$uiLight();
        int empty = SakuraVisualsClient.CONFIG.uiStyle == 1 ? 0xFF563644 : 0xFF39343A;

        int maxHearts = Math.max(1, (int) Math.ceil(maxHealth / 2.0F));
        int heartPoints = Math.max(0, health);
        int absorptionPoints = Math.max(0, absorption);

        for (int i = 0; i < maxHearts; i++) {
            int row = i / 10;
            int col = i % 10;
            int hx = x + col * 8;
            int hy = y - row * 10;
            int pointsLeft = heartPoints - i * 2;
            boolean full = pointsLeft >= 2;
            boolean half = pointsLeft == 1;
            sakuraVisuals$heart(graphics, hx, hy, empty, accent, light, full, half, blinking && i == regeneratingHeartIndex);
        }

        int absorptionHearts = (int) Math.ceil(absorptionPoints / 2.0F);
        for (int i = 0; i < absorptionHearts; i++) {
            int index = maxHearts + i;
            int row = index / 10;
            int col = index % 10;
            int hx = x + col * 8;
            int hy = y - row * 10;
            int pointsLeft = absorptionPoints - i * 2;
            sakuraVisuals$heart(graphics, hx, hy, empty, light, 0xFFFFFFFF,
                    pointsLeft >= 2, pointsLeft == 1, false);
        }

        ci.cancel();
    }

    private static int sakuraVisuals$uiAccent() {
        return SakuraVisualsClient.CONFIG.uiStyle == 1 ? 0xFFFF7FB5 : SakuraVisualsClient.accent();
    }

    private static int sakuraVisuals$uiLight() {
        return SakuraVisualsClient.CONFIG.uiStyle == 1 ? 0xFFFFD5E6 : SakuraVisualsClient.accentLight();
    }

    private static void sakuraVisuals$heart(GuiGraphics g, int x, int y, int empty, int fill, int highlight,
                                             boolean full, boolean half, boolean blink) {
        int[][] pixels = {
                {1, 1}, {2, 1}, {4, 1}, {5, 1},
                {0, 2}, {1, 2}, {2, 2}, {3, 2}, {4, 2}, {5, 2}, {6, 2},
                {0, 3}, {1, 3}, {2, 3}, {3, 3}, {4, 3}, {5, 3}, {6, 3},
                {1, 4}, {2, 4}, {3, 4}, {4, 4}, {5, 4},
                {2, 5}, {3, 5}, {4, 5},
                {3, 6}
        };

        for (int[] p : pixels) {
            g.fill(x + 1 + p[0], y + 1 + p[1], x + 2 + p[0], y + 2 + p[1], empty);
        }

        if (full || half) {
            int color = blink ? highlight : fill;
            for (int[] p : pixels) {
                if (!half || p[0] <= 3) {
                    g.fill(x + 1 + p[0], y + 1 + p[1], x + 2 + p[0], y + 2 + p[1], color);
                }
            }
            g.fill(x + 2, y + 2, x + 4, y + 3, highlight);
        }
    }

    private static void sakuraVisuals$blossom(GuiGraphics g, int x, int y, int color) {
        g.fill(x, y + 1, x + 2, y + 3, color);
        g.fill(x + 1, y, x + 3, y + 2, color);
        g.fill(x + 1, y + 2, x + 3, y + 4, color);
        g.fill(x + 2, y + 1, x + 4, y + 3, color);
        g.fill(x + 1, y + 1, x + 3, y + 3, 0xFFFFFFFF);
    }
}
