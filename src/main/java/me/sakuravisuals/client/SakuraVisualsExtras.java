package me.sakuravisuals.client;

import com.mojang.blaze3d.vertex.PoseStack;
import com.mojang.blaze3d.vertex.VertexConsumer;
import net.fabricmc.api.ClientModInitializer;
import net.fabricmc.fabric.api.client.event.lifecycle.v1.ClientTickEvents;
import net.fabricmc.fabric.api.client.rendering.v1.hud.HudElementRegistry;
import net.fabricmc.fabric.api.client.rendering.v1.world.WorldRenderContext;
import net.fabricmc.fabric.api.client.rendering.v1.world.WorldRenderEvents;
import net.minecraft.client.Minecraft;
import net.minecraft.client.gui.GuiGraphics;
import net.minecraft.client.gui.components.PlayerFaceRenderer;
import net.minecraft.client.renderer.rendertype.RenderTypes;
import net.minecraft.core.particles.ColorParticleOption;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.resources.Identifier;
import net.minecraft.world.phys.Vec3;
import org.joml.Vector3f;

public final class SakuraVisualsExtras implements ClientModInitializer {
    private static int trailTick;
    private static double lastX = Double.NaN;
    private static double lastZ = Double.NaN;

    @Override
    public void onInitializeClient() {
        ClientTickEvents.END_CLIENT_TICK.register(SakuraVisualsExtras::tickTrail);
        WorldRenderEvents.BEFORE_TRANSLUCENT.register(SakuraVisualsExtras::renderGeometricLine);
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

        double x = mc.player.getX();
        double y = mc.player.getY();
        double z = mc.player.getZ();

        // Line mode is true geometry. No particles are spawned here.
        if (Math.floorMod(SakuraVisualsClient.CONFIG.trailMode, 2) == 1) {
            lastX = x;
            lastZ = z;
            return;
        }

        // Sakura petal mode stays available as the second effect.
        if (trailTick % 3 != 0) return;
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
        spawnPetalColumn(mc, x + backX * 0.25D, y, z + backZ * 0.25D);
    }

    private static void spawnPetalColumn(Minecraft mc, double x, double y, double z) {
        int count = 12;
        double radius = 0.16D;
        ColorParticleOption petal = ColorParticleOption.create(
                ParticleTypes.TINTED_LEAVES, 0xFFFFECF5);

        for (int i = 0; i < count; i++) {
            double t = i / (double) (count - 1);
            double yy = y + 0.05D + t * 1.80D;
            double phase = trailTick * 0.46D + i * 1.60D;
            double ox = Math.sin(phase) * radius;
            double oz = Math.cos(phase) * radius;
            mc.level.addParticle(petal, x + ox, yy, z + oz, 0.0D, 0.008D, 0.0D);
        }
    }

    private static void renderGeometricLine(WorldRenderContext context) {
        Minecraft mc = Minecraft.getInstance();
        if (mc == null || mc.player == null || mc.level == null || !SakuraVisualsClient.CONFIG.playerTrail) return;
        if (Math.floorMod(SakuraVisualsClient.CONFIG.trailMode, 2) != 1) return;

        double yaw = Math.toRadians(mc.player.getYRot());

        // Keep the line close to the player, but move it slightly to the side and back.
        // This prevents the player's body from completely hiding it in third person.
        double backX = Math.sin(yaw) * 0.16D;
        double backZ = -Math.cos(yaw) * 0.16D;
        double sideX = Math.cos(yaw) * 0.38D;
        double sideZ = Math.sin(yaw) * 0.38D;

        Vec3 camera = context.worldState().cameraRenderState.pos;
        float x = (float) (mc.player.getX() + backX + sideX - camera.x);
        float z = (float) (mc.player.getZ() + backZ + sideZ - camera.z);
        float bottomY = (float) (mc.player.getY() + 0.02D - camera.y);
        float topY = (float) (mc.player.getY() + 1.90D - camera.y);

        PoseStack matrices = context.matrices();
        if (matrices == null) return;
        PoseStack.Pose pose = matrices.last();
        VertexConsumer line = context.consumers().getBuffer(RenderTypes.lines());

        int base = SakuraVisualsClient.accent();
        int light = SakuraVisualsClient.accentVeryLight();
        int glowColor = (0xA0 << 24) | (light & 0x00FFFFFF);
        int coreColor = 0xFF000000 | (base & 0x00FFFFFF);

        // IMPORTANT: the line shader needs a normal perpendicular to the vertical segment.
        // The old code used (0,1,0), parallel to the line, which could make it effectively invisible.
        Vector3f normal = new Vector3f((float) sideX, 0.0F, (float) sideZ);
        if (normal.lengthSquared() < 0.0001F) normal.set(1.0F, 0.0F, 0.0F);
        normal.normalize();

        // One geometric line, drawn twice on the exact same path: soft glow + crisp core.
        addLine(line, pose, x, bottomY, z, x, topY, z, glowColor, 9.0F, normal);
        addLine(line, pose, x, bottomY, z, x, topY, z, coreColor, 3.0F, normal);
    }

    private static void addLine(
            VertexConsumer consumer,
            PoseStack.Pose pose,
            float x0, float y0, float z0,
            float x1, float y1, float z1,
            int color,
            float width,
            Vector3f normal
    ) {
        consumer.addVertex(pose, x0, y0, z0)
                .setColor(color)
                .setNormal(pose, normal)
                .setLineWidth(width);
        consumer.addVertex(pose, x1, y1, z1)
                .setColor(color)
                .setNormal(pose, normal)
                .setLineWidth(width);
    }

    static int playerCardBaseWidth(Minecraft mc) {
        if (mc == null || mc.player == null) return 170;
        return Math.max(170, mc.font.width(mc.player.getName().getString()) + 82);
    }

    static int playerCardBaseHeight() {
        return 51;
    }

    private static void renderSkinCard(GuiGraphics g) {
        Minecraft mc = Minecraft.getInstance();
        if (mc.player == null || mc.level == null || mc.options.hideGui || !SakuraVisualsClient.CONFIG.playerCard) return;

        String name = mc.player.getName().getString();
        float hp = mc.player.getHealth();
        float maxHp = Math.max(1.0F, mc.player.getMaxHealth());
        float ratio = Math.max(0.0F, Math.min(1.0F, hp / maxHp));

        int accent = SakuraVisualsClient.accent();
        int light = SakuraVisualsClient.accentLight();
        int width = playerCardBaseWidth(mc);
        int height = playerCardBaseHeight();
        int head = 32;
        float scale = SakuraVisualsClient.clampScale(SakuraVisualsClient.CONFIG.playerCardScale);

        var matrices = g.pose();
        matrices.pushMatrix();
        matrices.translate(SakuraVisualsClient.CONFIG.playerCardX, SakuraVisualsClient.CONFIG.playerCardY);
        matrices.scale(scale, scale);

        g.fill(0, 0, width, height, 0xEC120C18);
        g.fill(0, 0, 3, height, accent);
        g.fill(3, 0, width, 2, 0x66FFFFFF & light | 0x66000000);

        g.fill(7, 7, 7 + head + 4, 7 + head + 4, 0xFF2A1825);
        g.fill(8, 8, 8 + head + 2, 8 + head + 2, accent);
        PlayerFaceRenderer.draw(g, mc.player.getSkin(), 10, 10, head - 2);

        int tx = 48;
        g.drawString(mc.font, name, tx, 8, light, true);
        g.drawString(mc.font, String.format("HP %.1f / %.1f", hp, maxHp), tx, 21, 0xFFFFFFFF, true);

        int barW = Math.max(54, width - tx - 10);
        int fillW = (int) (barW * ratio);
        int barY = 36;
        g.fill(tx, barY, tx + barW, barY + 8, 0xFF291922);
        g.fill(tx, barY, tx + fillW, barY + 8, accent);
        g.fill(tx, barY, tx + fillW, barY + 3, light);

        SakuraVisualsClient.blossom(g, width - 14, 7);
        SakuraVisualsClient.blossom(g, width - 23, height - 12);

        matrices.popMatrix();
    }
}
