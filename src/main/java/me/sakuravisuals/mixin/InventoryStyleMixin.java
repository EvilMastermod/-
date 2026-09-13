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

    @Inject(method = "render", at = @At("TAIL"))
    private void sakuraVisuals$decorateInventory(GuiGraphics graphics, int mouseX, int mouseY, float delta, CallbackInfo ci) {
        if (!((Object) this instanceof InventoryScreen)) return;

        int x0 = leftPos - 5;
        int y0 = topPos - 5;
        int x1 = leftPos + imageWidth + 5;
        int y1 = topPos + imageHeight + 5;

        if (SakuraVisualsClient.CONFIG.uiStyle == 1) {
            int pink = 0xFFFF7FB5;
            int light = 0xFFFFD5E6;
            int dark = 0xFF5B2E43;

            // Sakura frame: layered pink border outside the vanilla inventory.
            sakuraVisuals$outline(graphics, x0, y0, x1, y1, dark, 2);
            sakuraVisuals$outline(graphics, x0 + 2, y0 + 2, x1 - 2, y1 - 2, pink, 1);
            sakuraVisuals$outline(graphics, x0 + 4, y0 + 4, x1 - 4, y1 - 4, light, 1);

            sakuraVisuals$blossom(graphics, x0 - 3, y0 - 3, light);
            sakuraVisuals$blossom(graphics, x1 - 4, y0 - 3, light);
            sakuraVisuals$blossom(graphics, x0 - 3, y1 - 4, light);
            sakuraVisuals$blossom(graphics, x1 - 4, y1 - 4, light);

            // A few petal pixels around the frame for the blossom style.
            graphics.fill(x0 + 18, y0 - 4, x0 + 21, y0 - 2, pink);
            graphics.fill(x1 - 28, y0 - 3, x1 - 26, y0, light);
            graphics.fill(x0 - 3, y1 - 30, x0 - 1, y1 - 27, light);
            graphics.fill(x1 + 1, y0 + 28, x1 + 3, y0 + 31, pink);
        } else {
            int accent = SakuraVisualsClient.accent();
            int light = SakuraVisualsClient.accentLight();
            int woodDark = 0xFF4D3527;
            int wood = 0xFF8B623D;

            // Normal style stays vanilla-like, but receives the chosen accent color.
            sakuraVisuals$outline(graphics, x0, y0, x1, y1, woodDark, 2);
            sakuraVisuals$outline(graphics, x0 + 2, y0 + 2, x1 - 2, y1 - 2, wood, 1);
            sakuraVisuals$outline(graphics, x0 + 4, y0 + 4, x1 - 4, y1 - 4, accent, 1);

            sakuraVisuals$corner(graphics, x0 - 2, y0 - 2, accent, light);
            sakuraVisuals$corner(graphics, x1 - 6, y0 - 2, accent, light);
            sakuraVisuals$corner(graphics, x0 - 2, y1 - 6, accent, light);
            sakuraVisuals$corner(graphics, x1 - 6, y1 - 6, accent, light);
        }
    }

    private static void sakuraVisuals$outline(GuiGraphics g, int x0, int y0, int x1, int y1, int color, int size) {
        g.fill(x0, y0, x1, y0 + size, color);
        g.fill(x0, y1 - size, x1, y1, color);
        g.fill(x0, y0, x0 + size, y1, color);
        g.fill(x1 - size, y0, x1, y1, color);
    }

    private static void sakuraVisuals$corner(GuiGraphics g, int x, int y, int accent, int light) {
        g.fill(x, y, x + 6, y + 6, 0xFF3A2A22);
        g.fill(x + 1, y + 1, x + 5, y + 5, accent);
        g.fill(x + 2, y + 2, x + 4, y + 4, light);
    }

    private static void sakuraVisuals$blossom(GuiGraphics g, int x, int y, int color) {
        g.fill(x, y + 2, x + 2, y + 4, color);
        g.fill(x + 2, y, x + 4, y + 2, color);
        g.fill(x + 2, y + 4, x + 4, y + 6, color);
        g.fill(x + 4, y + 2, x + 6, y + 4, color);
        g.fill(x + 2, y + 2, x + 4, y + 4, 0xFFFFF4C5);
    }
}
