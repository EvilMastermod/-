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
        int dark = SakuraVisualsClient.CONFIG.uiStyle == 1 ? 0xFF4B2439 : 0xFF20232A;
        int x = graphics.guiWidth() / 2 - 91;
        int y = graphics.guiHeight() - 22;

        // Full decorative hotbar frame matching the selected inventory style.
        graphics.fill(x - 4, y - 4, x + 186, y + 25, dark);
        graphics.fill(x - 2, y - 2, x + 184, y + 23, 0x66100B15);

        for (int slot = 0; slot < 9; slot++) {
            int sx = x + 1 + slot * 20;
            int border = slot == Math.floorMod(mc.player.getInventory().getSelectedSlot(), 9) ? light : accent;
            int inner = slot == Math.floorMod(mc.player.getInventory().getSelectedSlot(), 9) ? accent : 0x66302A31;

            graphics.fill(sx - 1, y - 1, sx + 20, y, border);
            graphics.fill(sx - 1, y + 20, sx + 20, y + 21, border);
            graphics.fill(sx - 1, y - 1, sx, y + 21, border);
            graphics.fill(sx + 19, y - 1, sx + 20, y + 21, border);
            graphics.fill(sx + 1, y + 1, sx + 18, y + 2, inner);
        }

        // Stronger selected slot glow.
        int selected = Math.floorMod(mc.player.getInventory().getSelectedSlot(), 9);
        int sx = x + 1 + selected * 20;
        graphics.fill(sx - 2, y - 2, sx + 21, y - 1, light);
        graphics.fill(sx - 2, y + 21, sx + 21, y + 22, light);
        graphics.fill(sx - 2, y - 2, sx - 1, y + 22, light);
        graphics.fill(sx + 20, y - 2, sx + 21, y + 22, light);

        if (SakuraVisualsClient.CONFIG.uiStyle == 1) {
            sakuraVisuals$blossom(graphics, x - 7, y - 7, light);
            sakuraVisuals$blossom(graphics, x + 181, y - 7, light);
            sakuraVisuals$blossom(graphics, x - 7, y + 19, light);
            sakuraVisuals$blossom(graphics, x + 181, y + 19, light);
            sakuraVisuals$petal(graphics, x + 28, y - 5, accent);
            sakuraVisuals$petal(graphics, x + 145, y + 23, light);
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
        return SakuraVisualsClient.CONFIG.uiStyle == 1 ? 0xFFFF72AE : SakuraVisualsClient.accent();
    }

    private static int sakuraVisuals$uiLight() {
        return SakuraVisualsClient.CONFIG.uiStyle == 1 ? 0xFFFFD9E9 : SakuraVisualsClient.accentLight();
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

    private static void sakuraVisuals$petal(GuiGraphics g, int x, int y, int color) {
        g.fill(x, y, x + 3, y + 1, color);
        g.fill(x + 1, y + 1, x + 3, y + 2, color);
    }
}
