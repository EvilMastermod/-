package me.sakuravisuals.mixin;

import me.sakuravisuals.client.SakuraVisualsClient;
import net.minecraft.client.gui.GuiGraphics;
import net.minecraft.client.gui.components.Button;
import net.minecraft.client.gui.screens.Screen;
import net.minecraft.network.chat.Component;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.Unique;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;

import java.lang.reflect.Field;

@Mixin(targets = "me.sakuravisuals.client.SakuraVisualsClient$VisualsScreen")
public abstract class UiStyleScreenMixin extends Screen {
    protected UiStyleScreenMixin(Component title) {
        super(title);
    }

    @Inject(method = "init", at = @At("TAIL"))
    private void sakuraVisuals$addUiStyleButton(CallbackInfo ci) {
        if (!sakuraVisuals$isSakuraTab()) return;
        Layout l = sakuraVisuals$layout();
        int right = l.panelX + 20 + l.cardW + l.gapX;
        int row4 = l.panelY + l.header + 3 * (l.cardH + l.gapY);

        Button button = Button.builder(Component.empty(), b -> {
            SakuraVisualsClient.CONFIG.uiStyle = (SakuraVisualsClient.CONFIG.uiStyle + 1) % 2;
            SakuraVisualsClient.CONFIG.save();
        }).bounds(right, row4, l.cardW, l.cardH).build();
        button.setAlpha(0.0F);
        addRenderableWidget(button);
    }

    @Inject(method = "render", at = @At("TAIL"))
    private void sakuraVisuals$drawUiStyleButton(GuiGraphics g, int mouseX, int mouseY, float delta, CallbackInfo ci) {
        if (!sakuraVisuals$isSakuraTab()) return;
        Layout l = sakuraVisuals$layout();
        int right = l.panelX + 20 + l.cardW + l.gapX;
        int row4 = l.panelY + l.header + 3 * (l.cardH + l.gapY);
        int accent = SakuraVisualsClient.CONFIG.uiStyle == 1 ? 0xFFFF7FB5 : SakuraVisualsClient.accent();
        int light = SakuraVisualsClient.CONFIG.uiStyle == 1 ? 0xFFFFD5E6 : SakuraVisualsClient.accentLight();

        g.fill(right, row4, right + l.cardW, row4 + l.cardH, 0xEE100B17);
        g.fill(right, row4, right + l.cardW, row4 + 1, 0x66000000 | (accent & 0x00FFFFFF));
        g.drawString(font, "Стиль GUI", right + 8, row4 + 6, 0xFFFFFFFF, true);
        g.drawString(font, SakuraVisualsClient.CONFIG.uiStyle == 1 ? "Сакура" : "Обычный",
                right + 8, row4 + Math.max(17, l.cardH - 13), light, false);

        int bx = right + l.cardW - 30;
        int by = row4 + (l.cardH - 20) / 2;
        g.fill(bx, by, bx + 24, by + 20, 0xFF34272B);
        g.fill(bx + 2, by + 2, bx + 22, by + 18, accent);
        g.drawCenteredString(font, Component.literal(">"), bx + 12, by + 6, 0xFFFFFFFF);
    }

    @Unique
    private boolean sakuraVisuals$isSakuraTab() {
        try {
            Field field = getClass().getDeclaredField("tab");
            field.setAccessible(true);
            Object value = field.get(this);
            return value != null && "SAKURA".equals(value.toString());
        } catch (Throwable ignored) {
            return false;
        }
    }

    @Unique
    private Layout sakuraVisuals$layout() {
        int size = Math.floorMod(SakuraVisualsClient.CONFIG.menuSize, 3);
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
        return new Layout(panelX, panelY, cardW, cardH, gapX, gapY, header);
    }

    @Unique
    private record Layout(int panelX, int panelY, int cardW, int cardH, int gapX, int gapY, int header) {
    }
}
