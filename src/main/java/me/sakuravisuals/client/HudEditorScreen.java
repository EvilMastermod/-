package me.sakuravisuals.client;

import net.minecraft.client.Minecraft;
import net.minecraft.client.gui.GuiGraphics;
import net.minecraft.client.gui.components.Button;
import net.minecraft.client.gui.screens.Screen;
import net.minecraft.client.input.MouseButtonEvent;
import net.minecraft.network.chat.Component;

public final class HudEditorScreen extends Screen {
    private enum Block { INFO, PLAYER }

    private final Screen parent;
    private Block active;
    private boolean resizing;
    private double dragOffsetX;
    private double dragOffsetY;

    public HudEditorScreen(Screen parent) {
        super(Component.literal("Редактор HUD"));
        this.parent = parent;
    }

    @Override
    protected void init() {
        Button done = Button.builder(Component.empty(), b -> onClose())
                .bounds(this.width / 2 - 70, this.height - 34, 140, 24)
                .build();
        done.setAlpha(0.0F);
        addRenderableWidget(done);
    }

    @Override
    public void render(GuiGraphics g, int mouseX, int mouseY, float delta) {
        g.fill(0, 0, width, height, 0x66000000);
        g.fill(0, 0, width, 28, 0xCC110C18);
        g.drawCenteredString(font, Component.literal("Редактор HUD — тяни блок мышкой, уголок меняет размер"),
                width / 2, 9, 0xFFFFFFFF);

        drawBox(g, Block.INFO, "Инфо HUD");
        drawBox(g, Block.PLAYER, "Игрок HUD");

        int bx = width / 2 - 70;
        int by = height - 34;
        g.fill(bx, by, bx + 140, by + 24, 0xFF2F202C);
        g.fill(bx + 2, by + 2, bx + 138, by + 22, SakuraVisualsClient.accent());
        g.fill(bx + 2, by + 2, bx + 138, by + 11, SakuraVisualsClient.accentLight());
        g.drawCenteredString(font, Component.literal("Готово"), width / 2, by + 8, 0xFFFFFFFF);

        super.render(g, mouseX, mouseY, delta);
    }

    private void drawBox(GuiGraphics g, Block block, String title) {
        Rect r = rect(block);
        int c = SakuraVisualsClient.accent();
        int light = SakuraVisualsClient.accentLight();

        g.fill(r.x, r.y, r.x + r.w, r.y + 2, c);
        g.fill(r.x, r.y + r.h - 2, r.x + r.w, r.y + r.h, c);
        g.fill(r.x, r.y, r.x + 2, r.y + r.h, c);
        g.fill(r.x + r.w - 2, r.y, r.x + r.w, r.y + r.h, c);

        g.fill(r.x + r.w - 11, r.y + r.h - 11, r.x + r.w, r.y + r.h, light);
        g.fill(r.x + r.w - 8, r.y + r.h - 8, r.x + r.w - 2, r.y + r.h - 2, c);
        g.drawString(font, title, r.x + 5, r.y + 5, 0xFFFFFFFF, true);
    }

    @Override
    public boolean mouseClicked(MouseButtonEvent event, boolean doubleClick) {
        if (event.button() == 0) {
            double mx = event.x();
            double my = event.y();

            Block hit = hitBlock(mx, my);
            if (hit != null) {
                active = hit;
                Rect r = rect(hit);
                resizing = mx >= r.x + r.w - 14 && my >= r.y + r.h - 14;
                dragOffsetX = mx - r.x;
                dragOffsetY = my - r.y;
                return true;
            }
        }
        return super.mouseClicked(event, doubleClick);
    }

    @Override
    public boolean mouseDragged(MouseButtonEvent event, double dragX, double dragY) {
        if (active != null && event.button() == 0) {
            double mx = event.x();
            double my = event.y();
            if (resizing) {
                resize(active, mx, my);
            } else {
                move(active, mx - dragOffsetX, my - dragOffsetY);
            }
            return true;
        }
        return super.mouseDragged(event, dragX, dragY);
    }

    @Override
    public boolean mouseReleased(MouseButtonEvent event) {
        if (active != null && event.button() == 0) {
            active = null;
            resizing = false;
            SakuraVisualsClient.CONFIG.save();
            return true;
        }
        return super.mouseReleased(event);
    }

    private Block hitBlock(double x, double y) {
        Rect player = rect(Block.PLAYER);
        if (player.contains(x, y)) return Block.PLAYER;
        Rect info = rect(Block.INFO);
        if (info.contains(x, y)) return Block.INFO;
        return null;
    }

    private Rect rect(Block block) {
        Minecraft mc = Minecraft.getInstance();
        if (block == Block.INFO) {
            float scale = SakuraVisualsClient.clampScale(SakuraVisualsClient.CONFIG.hudInfoScale);
            int w = Math.max(60, Math.round(SakuraVisualsClient.hudInfoBaseWidth(mc) * scale));
            int h = Math.max(24, Math.round(SakuraVisualsClient.hudInfoBaseHeight(mc) * scale));
            return new Rect(SakuraVisualsClient.CONFIG.hudInfoX, SakuraVisualsClient.CONFIG.hudInfoY, w, h);
        }

        float scale = SakuraVisualsClient.clampScale(SakuraVisualsClient.CONFIG.playerCardScale);
        int w = Math.max(90, Math.round(SakuraVisualsExtras.playerCardBaseWidth(mc) * scale));
        int h = Math.max(30, Math.round(SakuraVisualsExtras.playerCardBaseHeight() * scale));
        return new Rect(SakuraVisualsClient.CONFIG.playerCardX, SakuraVisualsClient.CONFIG.playerCardY, w, h);
    }

    private void move(Block block, double x, double y) {
        Rect r = rect(block);
        int nx = clamp((int) Math.round(x), 0, Math.max(0, width - r.w));
        int ny = clamp((int) Math.round(y), 28, Math.max(28, height - r.h - 40));
        if (block == Block.INFO) {
            SakuraVisualsClient.CONFIG.hudInfoX = nx;
            SakuraVisualsClient.CONFIG.hudInfoY = ny;
        } else {
            SakuraVisualsClient.CONFIG.playerCardX = nx;
            SakuraVisualsClient.CONFIG.playerCardY = ny;
        }
    }

    private void resize(Block block, double mouseX, double mouseY) {
        Minecraft mc = Minecraft.getInstance();
        int x;
        int y;
        int baseW;
        int baseH;
        if (block == Block.INFO) {
            x = SakuraVisualsClient.CONFIG.hudInfoX;
            y = SakuraVisualsClient.CONFIG.hudInfoY;
            baseW = SakuraVisualsClient.hudInfoBaseWidth(mc);
            baseH = SakuraVisualsClient.hudInfoBaseHeight(mc);
        } else {
            x = SakuraVisualsClient.CONFIG.playerCardX;
            y = SakuraVisualsClient.CONFIG.playerCardY;
            baseW = SakuraVisualsExtras.playerCardBaseWidth(mc);
            baseH = SakuraVisualsExtras.playerCardBaseHeight();
        }

        float sx = (float) ((mouseX - x) / Math.max(1.0, baseW));
        float sy = (float) ((mouseY - y) / Math.max(1.0, baseH));
        float scale = Math.max(sx, sy);
        int percent = clamp(Math.round(scale * 100.0F), 55, 190);
        if (block == Block.INFO) SakuraVisualsClient.CONFIG.hudInfoScale = percent;
        else SakuraVisualsClient.CONFIG.playerCardScale = percent;
    }

    @Override
    public void onClose() {
        SakuraVisualsClient.CONFIG.save();
        if (minecraft != null) minecraft.setScreen(parent);
    }

    private static int clamp(int value, int min, int max) {
        return Math.max(min, Math.min(max, value));
    }

    private record Rect(int x, int y, int w, int h) {
        boolean contains(double px, double py) {
            return px >= x && py >= y && px <= x + w && py <= y + h;
        }
    }
}
