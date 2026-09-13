package me.sakuravisuals.client;

import net.fabricmc.api.ClientModInitializer;
import net.fabricmc.fabric.api.client.event.lifecycle.v1.ClientTickEvents;
import net.fabricmc.fabric.api.client.rendering.v1.hud.HudElementRegistry;
import net.minecraft.client.Minecraft;
import net.minecraft.client.gui.GuiGraphics;
import net.minecraft.client.gui.components.PlayerFaceRenderer;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.resources.Identifier;

public final class SakuraVisualsExtras implements ClientModInitializer {
    private static final int[] COLORS = {0xFFFF82BA, 0xFF72C7FF, 0xFFB38CFF, 0xFF72DEBE, 0xFFF4F4F4};
    private static final int[] LIGHT = {0xFFFFC7E0, 0xFFCCE9FF, 0xFFE3D3FF, 0xFFC9F4E7, 0xFFFFFFFF};

    private static int trailTick;
    private static double lastX = Double.NaN;
    private static double lastZ = Double.NaN;

    @Override
    public void onInitializeClient() {
        ClientTickEvents.END_CLIENT_TICK.register(SakuraVisualsExtras::tickTrail);
        HudElementRegistry.addLast(
                Identifier.fromNamespaceAndPath(SakuraVisualsClient.MOD_ID, "player_card_skin"),
                (graphics, deltaTracker) -> renderSkinCard(graphics)
        );
    }

    private static void tickTrail(Minecraft mc) {
        if (mc == null || mc.player == null || mc.level == null || !SakuraVisualsClient.CONFIG.playerTrail) {
            lastX = Double.NaN;
            lastZ = Double.NaN;
            return;
        }

        trailTick++;
        if ((trailTick & 1) != 0) return;

        double x = mc.player.getX();
        double y = mc.player.getY();
        double z = mc.player.getZ();
        if (Double.isNaN(lastX)) {
            lastX = x;
            lastZ = z;
            return;
        }

        double dx = x - lastX;
        double dz = z - lastZ;
        lastX = x;
        lastZ = z;
        if (dx * dx + dz * dz < 0.0004D) return;

        double phase = trailTick * 0.72D;
        double ox = Math.sin(phase) * 0.16D;
        double oz = Math.cos(phase) * 0.16D;

        mc.level.addParticle(ParticleTypes.CHERRY_LEAVES,
                x + ox, y + 0.10D, z + oz,
                0.0D, 0.015D, 0.0D);

        if ((trailTick & 3) == 0) {
            mc.level.addParticle(ParticleTypes.CHERRY_LEAVES,
                    x - ox, y + 0.14D, z - oz,
                    0.0D, 0.010D, 0.0D);
        }
    }

    private static void renderSkinCard(GuiGraphics g) {
        Minecraft mc = Minecraft.getInstance();
        if (mc.player == null || mc.level == null || mc.options.hideGui || !SakuraVisualsClient.CONFIG.playerCard) return;

        int x = 8;
        int y = 8;
        int lineCount = 0;
        if (SakuraVisualsClient.CONFIG.watermark) lineCount++;
        if (SakuraVisualsClient.CONFIG.coordinates) lineCount++;
        if (SakuraVisualsClient.CONFIG.fps) lineCount++;
        if (SakuraVisualsClient.CONFIG.worldTime) lineCount++;
        int cardY = lineCount == 0 ? y : y + lineCount * 11 + 10;

        String name = mc.player.getName().getString();
        float hp = mc.player.getHealth();
        float maxHp = Math.max(1.0F, mc.player.getMaxHealth());
        float ratio = Math.max(0.0F, Math.min(1.0F, hp / maxHp));

        int accent = accent();
        int light = accentLight();
        int head = 28;
        int width = Math.max(158, mc.font.width(name) + 68);
        int height = 43;

        g.fill(x - 4, cardY - 4, x + width + 6, cardY + height, 0xEC120C18);
        g.fill(x - 4, cardY - 4, x - 2, cardY + height, accent);
        g.fill(x - 2, cardY - 2, x + width + 4, cardY + 11, 0x38FFFFFF);

        g.fill(x, cardY, x + head + 4, cardY + head + 4, 0xFF2A1825);
        g.fill(x + 1, cardY + 1, x + head + 3, cardY + head + 3, accent);
        PlayerFaceRenderer.draw(g, mc.player.getSkin(), x + 3, cardY + 3, head - 2);

        int tx = x + head + 10;
        g.drawString(mc.font, name, tx, cardY + 3, light, true);
        g.drawString(mc.font, String.format("HP %.1f / %.1f", hp, maxHp), tx, cardY + 15, 0xFFFFFFFF, true);

        int barW = Math.max(48, width - (tx - x) - 9);
        int fillW = (int) (barW * ratio);
        int barY = cardY + 29;
        g.fill(tx, barY, tx + barW, barY + 7, 0xFF291922);
        g.fill(tx, barY, tx + fillW, barY + 7, accent);
        g.fill(tx, barY, tx + fillW, barY + 3, light);

        blossom(g, x + width - 13, cardY + 5);
        blossom(g, x + width - 20, cardY + 33);
    }

    private static int accent() {
        return COLORS[Math.floorMod(SakuraVisualsClient.CONFIG.accentColorIndex, COLORS.length)];
    }

    private static int accentLight() {
        return LIGHT[Math.floorMod(SakuraVisualsClient.CONFIG.accentColorIndex, LIGHT.length)];
    }

    private static void blossom(GuiGraphics g, int x, int y) {
        g.fill(x, y + 1, x + 1, y + 2, 0xFFFFB1CA);
        g.fill(x + 1, y, x + 2, y + 1, 0xFFFFB1CA);
        g.fill(x + 1, y + 2, x + 2, y + 3, 0xFFFFB1CA);
        g.fill(x + 2, y + 1, x + 3, y + 2, 0xFFFFB1CA);
        g.fill(x + 1, y + 1, x + 2, y + 2, 0xFFFFE37A);
    }
}
