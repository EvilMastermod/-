package me.sakuravisuals.mixin;

import me.sakuravisuals.client.SakuraVisualsClient;
import net.minecraft.client.gui.GuiGraphics;
import net.minecraft.client.gui.screens.inventory.AbstractContainerScreen;
import net.minecraft.client.gui.screens.inventory.InventoryScreen;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.Shadow;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;

@Mixin(AbstractContainerScreen.class)
public abstract class InventoryStyleMixin {
    @Shadow protected int leftPos;
    @Shadow protected int topPos;
    @Shadow protected int imageWidth;
    @Shadow protected int imageHeight;

    @Inject(method = "renderContents", at = @At("HEAD"))
    private void sakuraVisuals$drawInventorySkin(GuiGraphics g, int mouseX, int mouseY, float delta, CallbackInfo ci) {
        if (!((Object) this instanceof InventoryScreen)) return;

        if (SakuraVisualsClient.CONFIG.uiStyle == 1) {
            sakuraVisuals$drawSakuraInventory(g);
        } else {
            sakuraVisuals$drawNormalInventory(g);
        }
    }

    private void sakuraVisuals$drawSakuraInventory(GuiGraphics g) {
        int x = leftPos;
        int y = topPos;
        int w = imageWidth;
        int h = imageHeight;

        int dark = 0xFF4B2439;
        int dark2 = 0xFF251724;
        int cream = 0xFFF5C8D8;
        int cream2 = 0xFFFFDDE8;
        int pink = 0xFFFF79B1;
        int pink2 = 0xFFFFB6D0;
        int slot = 0xFF3B2B38;
        int slot2 = 0xFF5A3A50;

        // Full Sakura panel, but keep the player preview area translucent so the model remains visible.
        sakuraVisuals$rect(g, x, y, w, 8, cream2);
        sakuraVisuals$rect(g, x, y + 8, 26, 72, cream);
        sakuraVisuals$rect(g, x + 77, y + 8, w - 77, 72, cream);
        sakuraVisuals$rect(g, x, y + 80, w, h - 80, cream);
        sakuraVisuals$rect(g, x + 26, y + 8, 51, 72, 0x99201422);

        // Thick layered blossom frame like the reference.
        sakuraVisuals$outline(g, x - 6, y - 6, x + w + 6, y + h + 6, dark, 3);
        sakuraVisuals$outline(g, x - 3, y - 3, x + w + 3, y + h + 3, pink, 2);
        sakuraVisuals$outline(g, x, y, x + w, y + h, pink2, 1);
        sakuraVisuals$outline(g, x + 2, y + 2, x + w - 2, y + h - 2, cream2, 1);

        // Player preview window.
        sakuraVisuals$outline(g, x + 25, y + 7, x + 78, y + 81, dark, 2);
        sakuraVisuals$outline(g, x + 27, y + 9, x + 76, y + 79, pink2, 1);

        // Armor slots.
        for (int i = 0; i < 4; i++) {
            sakuraVisuals$slot(g, x + 8, y + 8 + i * 18, slot, slot2, pink2, true);
        }

        // Crafting 2x2 and output.
        for (int row = 0; row < 2; row++) {
            for (int col = 0; col < 2; col++) {
                sakuraVisuals$slot(g, x + 98 + col * 18, y + 18 + row * 18, slot, slot2, pink2, true);
            }
        }
        sakuraVisuals$slot(g, x + 154, y + 28, slot, slot2, pink2, true);
        sakuraVisuals$slot(g, x + 77, y + 62, slot, slot2, pink2, true);

        // Main inventory and hotbar.
        for (int row = 0; row < 3; row++) {
            for (int col = 0; col < 9; col++) {
                sakuraVisuals$slot(g, x + 8 + col * 18, y + 84 + row * 18, slot, slot2, pink2, true);
            }
        }
        for (int col = 0; col < 9; col++) {
            sakuraVisuals$slot(g, x + 8 + col * 18, y + 142, slot, slot2, pink2, true);
        }

        // Decorative blossoms and branches.
        sakuraVisuals$blossom(g, x - 8, y - 8, cream2);
        sakuraVisuals$blossom(g, x + w - 1, y - 8, cream2);
        sakuraVisuals$blossom(g, x - 8, y + h - 1, cream2);
        sakuraVisuals$blossom(g, x + w - 1, y + h - 1, cream2);
        sakuraVisuals$blossom(g, x + 72, y - 5, pink2);
        sakuraVisuals$blossom(g, x + 70, y + h - 2, pink2);

        // Petal pixels around the frame.
        g.fill(x + 16, y - 7, x + 20, y - 5, pink);
        g.fill(x + 130, y - 6, x + 133, y - 3, cream2);
        g.fill(x - 6, y + 52, x - 3, y + 56, pink2);
        g.fill(x + w + 3, y + 34, x + w + 6, y + 37, pink);
        g.fill(x + w - 22, y + h + 3, x + w - 18, y + h + 5, cream2);

        // Small arrow between crafting and result.
        g.fill(x + 135, y + 35, x + 146, y + 37, dark);
        g.fill(x + 143, y + 32, x + 147, y + 40, dark);
        g.fill(x + 145, y + 34, x + 149, y + 38, pink);
    }

    private void sakuraVisuals$drawNormalInventory(GuiGraphics g) {
        int x = leftPos;
        int y = topPos;
        int w = imageWidth;
        int h = imageHeight;

        int accent = SakuraVisualsClient.accent();
        int light = SakuraVisualsClient.accentLight();
        int woodDark = 0xFF4A3020;
        int wood = 0xFF93663C;
        int woodLight = 0xFFC48A4A;
        int parchment = 0xFFE7C99D;
        int slot = 0xFF35353A;
        int slot2 = 0xFF4A494F;

        sakuraVisuals$rect(g, x, y, w, 8, parchment);
        sakuraVisuals$rect(g, x, y + 8, 26, 72, parchment);
        sakuraVisuals$rect(g, x + 77, y + 8, w - 77, 72, parchment);
        sakuraVisuals$rect(g, x, y + 80, w, h - 80, parchment);
        sakuraVisuals$rect(g, x + 26, y + 8, 51, 72, 0x88202024);

        // Wooden vanilla-like frame with chosen accent.
        sakuraVisuals$outline(g, x - 6, y - 6, x + w + 6, y + h + 6, woodDark, 3);
        sakuraVisuals$outline(g, x - 3, y - 3, x + w + 3, y + h + 3, wood, 2);
        sakuraVisuals$outline(g, x, y, x + w, y + h, woodLight, 1);
        sakuraVisuals$outline(g, x + 2, y + 2, x + w - 2, y + h - 2, accent, 1);

        sakuraVisuals$outline(g, x + 25, y + 7, x + 78, y + 81, woodDark, 2);
        sakuraVisuals$outline(g, x + 27, y + 9, x + 76, y + 79, accent, 1);

        for (int i = 0; i < 4; i++) sakuraVisuals$slot(g, x + 8, y + 8 + i * 18, slot, slot2, light, false);
        for (int row = 0; row < 2; row++) {
            for (int col = 0; col < 2; col++) sakuraVisuals$slot(g, x + 98 + col * 18, y + 18 + row * 18, slot, slot2, light, false);
        }
        sakuraVisuals$slot(g, x + 154, y + 28, slot, slot2, light, false);
        sakuraVisuals$slot(g, x + 77, y + 62, slot, slot2, light, false);
        for (int row = 0; row < 3; row++) {
            for (int col = 0; col < 9; col++) sakuraVisuals$slot(g, x + 8 + col * 18, y + 84 + row * 18, slot, slot2, accent, false);
        }
        for (int col = 0; col < 9; col++) sakuraVisuals$slot(g, x + 8 + col * 18, y + 142, slot, slot2, accent, false);

        sakuraVisuals$woodCorner(g, x - 9, y - 9, woodDark, woodLight, accent);
        sakuraVisuals$woodCorner(g, x + w - 1, y - 9, woodDark, woodLight, accent);
        sakuraVisuals$woodCorner(g, x - 9, y + h - 1, woodDark, woodLight, accent);
        sakuraVisuals$woodCorner(g, x + w - 1, y + h - 1, woodDark, woodLight, accent);

        g.fill(x + 135, y + 35, x + 146, y + 37, woodDark);
        g.fill(x + 143, y + 32, x + 147, y + 40, woodDark);
        g.fill(x + 145, y + 34, x + 149, y + 38, accent);
    }

    private static void sakuraVisuals$slot(GuiGraphics g, int x, int y, int fill, int inner, int border, boolean flower) {
        g.fill(x, y, x + 18, y + 18, border);
        g.fill(x + 1, y + 1, x + 17, y + 17, 0xFF20191F);
        g.fill(x + 2, y + 2, x + 16, y + 16, fill);
        g.fill(x + 3, y + 3, x + 15, y + 4, inner);
        if (flower) {
            g.fill(x + 8, y + 6, x + 10, y + 8, 0xFF9A617B);
            g.fill(x + 6, y + 8, x + 8, y + 10, 0xFF9A617B);
            g.fill(x + 10, y + 8, x + 12, y + 10, 0xFF9A617B);
            g.fill(x + 8, y + 10, x + 10, y + 12, 0xFF9A617B);
            g.fill(x + 8, y + 8, x + 10, y + 10, 0xFFFFD6E7);
        }
    }

    private static void sakuraVisuals$rect(GuiGraphics g, int x, int y, int w, int h, int color) {
        if (w > 0 && h > 0) g.fill(x, y, x + w, y + h, color);
    }

    private static void sakuraVisuals$outline(GuiGraphics g, int x0, int y0, int x1, int y1, int color, int size) {
        g.fill(x0, y0, x1, y0 + size, color);
        g.fill(x0, y1 - size, x1, y1, color);
        g.fill(x0, y0, x0 + size, y1, color);
        g.fill(x1 - size, y0, x1, y1, color);
    }

    private static void sakuraVisuals$woodCorner(GuiGraphics g, int x, int y, int dark, int wood, int accent) {
        g.fill(x, y, x + 10, y + 10, dark);
        g.fill(x + 2, y + 2, x + 8, y + 8, wood);
        g.fill(x + 4, y + 4, x + 6, y + 6, accent);
    }

    private static void sakuraVisuals$blossom(GuiGraphics g, int x, int y, int color) {
        g.fill(x, y + 2, x + 2, y + 4, color);
        g.fill(x + 2, y, x + 4, y + 2, color);
        g.fill(x + 2, y + 4, x + 4, y + 6, color);
        g.fill(x + 4, y + 2, x + 6, y + 4, color);
        g.fill(x + 2, y + 2, x + 4, y + 4, 0xFFFFF4C5);
    }
}
