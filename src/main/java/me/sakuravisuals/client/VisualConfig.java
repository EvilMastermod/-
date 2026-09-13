package me.sakuravisuals.client;

import net.fabricmc.loader.api.FabricLoader;

import java.io.IOException;
import java.io.InputStream;
import java.io.OutputStream;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.Properties;

public final class VisualConfig {
    public boolean watermark = true;
    public boolean coordinates = true;
    public boolean fps = true;
    public boolean worldTime = false;
    public boolean crosshair = true;
    public boolean sakuraPetals = true;
    public boolean hudBackground = true;
    public boolean fullBright = false;
    public boolean playerCard = true;
    public boolean playerTrail = true;
    public int accentColorIndex = 0;

    private final Path path = FabricLoader.getInstance().getConfigDir().resolve("sakuravisuals.properties");

    public void load() {
        if (!Files.exists(path)) return;
        Properties p = new Properties();
        try (InputStream in = Files.newInputStream(path)) {
            p.load(in);
            watermark = getBool(p, "watermark", watermark);
            coordinates = getBool(p, "coordinates", coordinates);
            fps = getBool(p, "fps", fps);
            worldTime = getBool(p, "worldTime", worldTime);
            crosshair = getBool(p, "crosshair", crosshair);
            sakuraPetals = getBool(p, "sakuraPetals", sakuraPetals);
            hudBackground = getBool(p, "hudBackground", hudBackground);
            fullBright = getBool(p, "fullBright", fullBright);
            playerCard = getBool(p, "playerCard", playerCard);
            playerTrail = getBool(p, "playerTrail", playerTrail);
            accentColorIndex = getInt(p, "accentColorIndex", accentColorIndex);
        } catch (IOException ignored) {
        }
    }

    public void save() {
        Properties p = new Properties();
        p.setProperty("watermark", Boolean.toString(watermark));
        p.setProperty("coordinates", Boolean.toString(coordinates));
        p.setProperty("fps", Boolean.toString(fps));
        p.setProperty("worldTime", Boolean.toString(worldTime));
        p.setProperty("crosshair", Boolean.toString(crosshair));
        p.setProperty("sakuraPetals", Boolean.toString(sakuraPetals));
        p.setProperty("hudBackground", Boolean.toString(hudBackground));
        p.setProperty("fullBright", Boolean.toString(fullBright));
        p.setProperty("playerCard", Boolean.toString(playerCard));
        p.setProperty("playerTrail", Boolean.toString(playerTrail));
        p.setProperty("accentColorIndex", Integer.toString(accentColorIndex));
        try {
            Files.createDirectories(path.getParent());
            try (OutputStream out = Files.newOutputStream(path)) {
                p.store(out, "Sakura Visuals settings");
            }
        } catch (IOException ignored) {
        }
    }

    private static boolean getBool(Properties p, String key, boolean fallback) {
        return Boolean.parseBoolean(p.getProperty(key, Boolean.toString(fallback)));
    }

    private static int getInt(Properties p, String key, int fallback) {
        try {
            return Integer.parseInt(p.getProperty(key, Integer.toString(fallback)));
        } catch (NumberFormatException ignored) {
            return fallback;
        }
    }
}
