#!/usr/bin/env python3
"""Replace the large left Pitbike Stunt overlay with a hotbar-side speed readout."""
from pathlib import Path

p = Path('project/src/main/java/dev/pitbike/stunt/client/PitbikeStuntClient.java')
src = p.read_text(encoding='utf-8')
start = src.index('        HudRenderCallback.EVENT.register((draw, counter) -> {')
end = src.index('        });', start) + len('        });')
new = '''        HudRenderCallback.EVENT.register((draw, counter) -> {
            MinecraftClient client = MinecraftClient.getInstance();
            if (client.player == null || client.options.hudHidden
                    || !(client.player.getVehicle() instanceof PitbikeEntity bike)) return;

            // Donor HUD location: speed right of the vanilla hotbar.
            int screenW = client.getWindow().getScaledWidth();
            int screenH = client.getWindow().getScaledHeight();
            int speedX = screenW / 2 + 96;
            int speedY = screenH - 20;
            draw.drawTextWithShadow(client.textRenderer,
                    Text.literal(String.format("§f%.0f §7km/h", bike.kmh())),
                    speedX, speedY, 0xFFFFFF);

            // Slim status at top; no left-side panel.
            String top = String.format("§d%s  §8|  §fG%d  §8|  §f%d RPM",
                    bike.variant().title, bike.gear(), bike.rpm());
            String mid = String.format("§7Fuel §f%.0f%%  §8|  §7Condition §f%d%%  §8|  §7Score §f%d",
                    bike.fuel(), bike.condition(), bike.score());
            int topX = Math.max(4, (screenW - client.textRenderer.getWidth(top)) / 2);
            int midX = Math.max(4, (screenW - client.textRenderer.getWidth(mid)) / 2);
            draw.drawTextWithShadow(client.textRenderer, Text.literal(top), topX, 6, 0xFFFFFF);
            draw.drawTextWithShadow(client.textRenderer, Text.literal(mid), midX, 19, 0xFFFFFF);

            if (bike.trick() != 0) {
                String performing = "§e" + TRICKS[Math.min(9, Math.max(0, bike.trick()))];
                int trickX = Math.max(4, (screenW - client.textRenderer.getWidth(performing)) / 2);
                draw.drawTextWithShadow(client.textRenderer, Text.literal(performing), trickX, 32, 0xFFFFFF);
            } else if (bike.kickstand()) {
                String parked = "§eKickstand DOWN";
                int parkedX = Math.max(4, (screenW - client.textRenderer.getWidth(parked)) / 2);
                draw.drawTextWithShadow(client.textRenderer, Text.literal(parked), parkedX, 32, 0xFFFFFF);
            }
        });'''
assert 'int x = 12, y = client.getWindow().getScaledHeight() - 116;' in src, 'Old left HUD missing'
src = src[:start] + new + src[end:]
assert '0xBA1A1525' not in src
p.write_text(src, encoding='utf-8')
print('Removed left HUD; speed beside hotbar; concise top status')
