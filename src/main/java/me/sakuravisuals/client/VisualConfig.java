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

    private final Path path = FabricLoader.getInstance().getConfigDir().resolve("sakuravisuals.properties");

    public void load() {
        if (!Files.exists(path)) return;
        Properties p = new Properties();
        try (InputStream in = Files.newInputStream(path)) {
            p.load(in);
            watermark = get(p, "watermark", watermark);
            coordinates = get(p, "coordinates", coordinates);
            fps = get(p, "fps", fps);
            worldTime = get(p, "worldTime", worldTime);
            crosshair = get(p, "crosshair", crosshair);
            sakuraPetals = get(p, "sakuraPetals", sakuraPetals);
            hudBackground = get(p, "hudBackground", hudBackground);
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
        try {
            Files.createDirectories(path.getParent());
            try (OutputStream out = Files.newOutputStream(path)) {
                p.store(out, "Sakura Visuals settings");
            }
        } catch (IOException ignored) {
        }
    }

    private static boolean get(Properties p, String key, boolean fallback) {
        return Boolean.parseBoolean(p.getProperty(key, Boolean.toString(fallback)));
    }
}
