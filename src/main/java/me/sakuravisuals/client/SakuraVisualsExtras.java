package me.sakuravisuals.client;

import net.fabricmc.api.ClientModInitializer;
import net.fabricmc.fabric.api.client.event.lifecycle.v1.ClientTickEvents;
import net.fabricmc.fabric.api.client.rendering.v1.hud.HudElementRegistry;
import net.minecraft.client.Minecraft;
import net.minecraft.client.gui.GuiGraphics;
import net.minecraft.client.gui.components.PlayerFaceRenderer;
import net.minecraft.core.particles.ColorParticleOption;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.resources.Identifier;

public final class SakuraVisualsExtras implements ClientModInitializer {
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
        int size = Math.floorMod(SakuraVisualsClient.CONFIG.trailSize, 3);
        int interval = size == 0 ? 3 : (size == 1 ? 2 : 1);
        if (trailTick % interval != 0) return;

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
        if (dx * dx + dz * dz < 0.00004D) return;

        double len = Math.sqrt(dx * dx + dz * dz);
        double backX = len > 0.00001D ? -dx / len : 0.0D;
        double backZ = len > 0.00001D ? -dz / len : 0.0D;
        double distance = size == 0 ? 0.18D : (size == 1 ? 0.28D : 0.38D);
        double px = x + backX * distance;
        double pz = z + backZ * distance;

        if (Math.floorMod(SakuraVisualsClient.CONFIG.trailMode, 2) == 0) {
            spawnPetalColumn(mc, px, y, pz, size);
        } else {
            spawnColorLine(mc, px, y, pz, size);
        }
    }

    private static void spawnPetalColumn(Minecraft mc, double x, double y, double z, int size) {
        int count = size == 0 ? 4 : (size == 1 ? 6 : 9);
        double radius = size == 0 ? 0.08D : (size == 1 ? 0.14D : 0.22D);
        ColorParticleOption option = ColorParticleOption.create(ParticleTypes.TINTED_LEAVES, SakuraVisualsClient.accent());

        for (int i = 0; i < count; i++) {
            double t = count <= 1 ? 0.0D : i / (double) (count - 1);
            double yy = y + 0.05D + t * 1.75D;
            double phase = trailTick * 0.44D + i * 1.73D;
            double ox = Math.sin(phase) * radius;
            double oz = Math.cos(phase) * radius;
            mc.level.addParticle(option, x + ox, yy, z + oz, 0.0D, 0.006D, 0.0D);
        }
    }

    private static void spawnColorLine(Minecraft mc, double x, double y, double z, int size) {
        int count = size == 0 ? 7 : (size == 1 ? 11 : 16);
        ColorParticleOption option = ColorParticleOption.create(ParticleTypes.TINTED_LEAVES, SakuraVisualsClient.accent());
        for (int i = 0; i < count; i++) {
            double t = count <= 1 ? 0.0D : i / (double) (count - 1);
            double yy = y + 0.04D + t * 1.78D;
            mc.level.addParticle(option, x, yy, z, 0.0D, 0.0D, 0.0D);
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

        int accent = SakuraVisualsClient.accent();
        int light = SakuraVisualsClient.accentLight();
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

        blossom(g, x + width - 13, cardY + 5, light);
        blossom(g, x + width - 20, cardY + 33, light);
    }

    private static void blossom(GuiGraphics g, int x, int y, int color) {
        g.fill(x, y + 1, x + 1, y + 2, color);
        g.fill(x + 1, y, x + 2, y + 1, color);
        g.fill(x + 1, y + 2, x + 2, y + 3, color);
        g.fill(x + 2, y + 1, x + 3, y + 2, color);
        g.fill(x + 1, y + 1, x + 2, y + 2, 0xFFFFFFFF);
    }
}
