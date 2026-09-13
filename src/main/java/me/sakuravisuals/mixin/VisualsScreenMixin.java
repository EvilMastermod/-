package me.sakuravisuals.mixin;

import me.sakuravisuals.client.SakuraVisualsClient;
import net.minecraft.client.gui.GuiGraphics;
import net.minecraft.client.gui.components.Button;
import net.minecraft.client.gui.screens.Screen;
import net.minecraft.network.chat.Component;
import net.minecraft.network.chat.FontDescription;
import net.minecraft.network.chat.Style;
import net.minecraft.resources.Identifier;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.Unique;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;

import java.lang.reflect.Field;

@Mixin(targets = "me.sakuravisuals.client.SakuraVisualsClient$VisualsScreen")
public abstract class VisualsScreenMixin extends Screen {
    @Unique private static final int WHITE = 0xFFFFFFFF;
    @Unique private static final int SOFT = 0xFFD9BAC7;
    @Unique private static final int BG = 0xE5120C19;
    @Unique private static final int PANEL = 0xF2191125;
    @Unique private static final int CARD = 0xEE100B17;
    @Unique private static final int BORDER = 0xFF34272B;
    @Unique private static final int PINK = 0xFFFFD5E3;
    @Unique private static final int PINK_TOP = 0xFFFFE7ED;
    @Unique private static final int PINK_ON = 0xFFE681AB;
    @Unique private static final int PINK_ON_TOP = 0xFFF29BBD;
    @Unique private static final String[] COLOR_NAMES = {"Розовый", "Голубой", "Фиолетовый", "Мятный", "Белый"};
    @Unique private static final int[] COLORS = {0xFFFF82BA, 0xFF72C7FF, 0xFFB38CFF, 0xFF72DEBE, 0xFFF4F4F4};
    @Unique private static final int[] LIGHT = {0xFFFFC7E0, 0xFFCCE9FF, 0xFFE3D3FF, 0xFFC9F4E7, 0xFFFFFFFF};
    @Unique private static final FontDescription.Resource SAKURA_FONT =
            new FontDescription.Resource(Identifier.fromNamespaceAndPath("minecraft", "uniform"));

    protected VisualsScreenMixin(Component title) { super(title); }

    @Inject(method = "init", at = @At("TAIL"))
    private void sakuraVisuals$addTrailToggle(CallbackInfo ci) {
        if (!sakuraVisuals$isSakuraTab()) return;
        int center = width / 2;
        int top = height / 2 - 120;
        int right = center + 8;
        int r3 = top + 158;
        Button b = Button.builder(Component.empty(), button -> {
                    SakuraVisualsClient.CONFIG.playerTrail = !SakuraVisualsClient.CONFIG.playerTrail;
                    SakuraVisualsClient.CONFIG.save();
                })
                .bounds(right, r3, 167, 32)
                .build();
        b.setAlpha(0.0F);
        addRenderableWidget(b);
    }

    @Inject(method = "render", at = @At("HEAD"), cancellable = true)
    private void sakuraVisuals$renderCustomFont(GuiGraphics g, int mouseX, int mouseY, float delta, CallbackInfo ci) {
        boolean sakura = sakuraVisuals$isSakuraTab();
        int center = width / 2;
        int top = height / 2 - 120;
        int left = center - 175;
        int right = center + 8;
        int r1 = top + 78;
        int r2 = top + 118;
        int r3 = top + 158;

        g.fill(0, 0, width, height, BG);
        g.fill(center - 200, top, center + 200, top + 245, PANEL);
        g.fill(center - 200, top, center + 200, top + 2, PINK_ON_TOP);
        g.fill(center - 200, top, center - 196, top + 245, 0xFFE28AAF);

        g.drawCenteredString(font, sakuraVisuals$text("SAKURA VISUALS"), center, top + 8, 0xFFFFD7E4);
        sakuraVisuals$bigButton(g, center - 175, top + 30, 165, 28, "КАСТОМ", !sakura);
        sakuraVisuals$bigButton(g, center + 10, top + 30, 165, 28, "САКУРА", sakura);

        if (!sakura) {
            sakuraVisuals$card(g, left, r1, "ПРИЦЕЛ", "Кастомный цветной", SakuraVisualsClient.CONFIG.crosshair);
            sakuraVisuals$card(g, right, r1, "ФУЛ БРАЙТ", "Без темноты и теней", SakuraVisualsClient.CONFIG.fullBright);
            sakuraVisuals$card(g, left, r2, "КООРДИНАТЫ", "Показывать XYZ", SakuraVisualsClient.CONFIG.coordinates);
            sakuraVisuals$card(g, right, r2, "FPS", "Показывать FPS", SakuraVisualsClient.CONFIG.fps);
            sakuraVisuals$colorCard(g, left, r3);
            sakuraVisuals$card(g, right, r3, "ФОН HUD", "Подложка у HUD", SakuraVisualsClient.CONFIG.hudBackground);
        } else {
            sakuraVisuals$card(g, left, r1, "ЛЕПЕСТКИ", "Сакура на экране", SakuraVisualsClient.CONFIG.sakuraPetals);
            sakuraVisuals$card(g, right, r1, "WATERMARK", "Sakura Visuals", SakuraVisualsClient.CONFIG.watermark);
            sakuraVisuals$card(g, left, r2, "ВРЕМЯ МИРА", "Игровые часы", SakuraVisualsClient.CONFIG.worldTime);
            sakuraVisuals$card(g, right, r2, "ФОН HUD", "Темная подложка", SakuraVisualsClient.CONFIG.hudBackground);
            sakuraVisuals$card(g, left, r3, "ИГРОК HUD", "Скин, ник и HP", SakuraVisualsClient.CONFIG.playerCard);
            sakuraVisuals$card(g, right, r3, "СЛЕД ИГРОКА", "Розовая сакура", SakuraVisualsClient.CONFIG.playerTrail);
        }

        sakuraVisuals$bigButton(g, center - 70, top + 207, 140, 26, "ГОТОВО", false);
        g.drawCenteredString(font, sakuraVisuals$text("BLOOM UI • RIGHT SHIFT"), center, top + 232, SOFT);
        ci.cancel();
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
    private Component sakuraVisuals$text(String text) {
        return Component.literal(text).setStyle(Style.EMPTY.withFont(SAKURA_FONT).withBold(true));
    }

    @Unique
    private void sakuraVisuals$card(GuiGraphics g, int x, int y, String title, String subtitle, boolean on) {
        g.fill(x, y, x + 167, y + 32, CARD);
        g.fill(x, y, x + 167, y + 1, 0x55433237);
        g.drawString(font, sakuraVisuals$text(title), x + 8, y + 7, WHITE, true);
        g.drawString(font, sakuraVisuals$text(subtitle), x + 8, y + 19, SOFT, true);
        sakuraVisuals$miniButton(g, x + 119, y + 6, 42, 20, on ? "ВКЛ" : "ВЫКЛ", on);
    }

    @Unique
    private void sakuraVisuals$colorCard(GuiGraphics g, int x, int y) {
        int idx = Math.floorMod(SakuraVisualsClient.CONFIG.accentColorIndex, COLORS.length);
        g.fill(x, y, x + 167, y + 32, CARD);
        g.drawString(font, sakuraVisuals$text("ЦВЕТ"), x + 8, y + 7, WHITE, true);
        g.drawString(font, sakuraVisuals$text(COLOR_NAMES[idx]), x + 8, y + 19, LIGHT[idx], true);
        g.fill(x + 112, y + 7, x + 159, y + 25, BORDER);
        g.fill(x + 114, y + 9, x + 157, y + 23, LIGHT[idx]);
        g.fill(x + 124, y + 15, x + 147, y + 16, COLORS[idx]);
        g.fill(x + 135, y + 11, x + 136, y + 21, COLORS[idx]);
    }

    @Unique
    private void sakuraVisuals$bigButton(GuiGraphics g, int x, int y, int w, int h, String text, boolean selected) {
        int base = selected ? PINK_ON : PINK;
        int top = selected ? PINK_ON_TOP : PINK_TOP;
        g.fill(x, y, x + w, y + h, BORDER);
        g.fill(x + 2, y + 2, x + w - 2, y + h - 2, base);
        g.fill(x + 2, y + 2, x + w - 2, y + h / 2, top);
        sakuraVisuals$blossom(g, x + 7, y + 7);
        sakuraVisuals$blossom(g, x + w - 13, y + h - 11);
        g.drawCenteredString(font, sakuraVisuals$text(text), x + w / 2, y + 9, 0xFF281314);
    }

    @Unique
    private void sakuraVisuals$miniButton(GuiGraphics g, int x, int y, int w, int h, String text, boolean pressed) {
        int base = pressed ? PINK_ON : PINK;
        int top = pressed ? PINK_ON_TOP : PINK_TOP;
        g.fill(x, y, x + w, y + h, BORDER);
        g.fill(x + 2, y + 2, x + w - 2, y + h - 2, base);
        g.fill(x + 2, y + 2, x + w - 2, y + h / 2, top);
        sakuraVisuals$blossom(g, x + 5, y + 5);
        g.drawCenteredString(font, sakuraVisuals$text(text), x + w / 2, y + 6, 0xFF291719);
    }

    @Unique
    private void sakuraVisuals$blossom(GuiGraphics g, int x, int y) {
        g.fill(x, y + 1, x + 1, y + 2, 0xFFFFB1CA);
        g.fill(x + 1, y, x + 2, y + 1, 0xFFFFB1CA);
        g.fill(x + 1, y + 2, x + 2, y + 3, 0xFFFFB1CA);
        g.fill(x + 2, y + 1, x + 3, y + 2, 0xFFFFB1CA);
        g.fill(x + 1, y + 1, x + 2, y + 2, 0xFFFFE37A);
    }
}
