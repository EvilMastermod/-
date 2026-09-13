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

    // 0 = petals, 1 = colored beam/wedge
    public int trailMode = 0;
    public int accentColorIndex = 0;

    // 0 = normal/vanilla inspired, 1 = sakura
    public int uiStyle = 1;

    // 0 = small, 1 = medium, 2 = large
    public int menuSize = 1;

    // Freely editable HUD placement and scale (percent).
    public int hudInfoX = 8;
    public int hudInfoY = 8;
    public int hudInfoScale = 100;
    public int playerCardX = 8;
    public int playerCardY = 72;
    public int playerCardScale = 100;

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
            trailMode = getInt(p, "trailMode", trailMode);
            accentColorIndex = getInt(p, "accentColorIndex", accentColorIndex);
            uiStyle = getInt(p, "uiStyle", uiStyle);
            menuSize = getInt(p, "menuSize", menuSize);
            hudInfoX = getInt(p, "hudInfoX", hudInfoX);
            hudInfoY = getInt(p, "hudInfoY", hudInfoY);
            hudInfoScale = getInt(p, "hudInfoScale", hudInfoScale);
            playerCardX = getInt(p, "playerCardX", playerCardX);
            playerCardY = getInt(p, "playerCardY", playerCardY);
            playerCardScale = getInt(p, "playerCardScale", playerCardScale);
        } catch (IOException ignored) {
        }

        menuSize = Math.floorMod(menuSize, 3);
        trailMode = Math.floorMod(trailMode, 2);
        uiStyle = Math.floorMod(uiStyle, 2);
        hudInfoScale = clamp(hudInfoScale, 55, 190);
        playerCardScale = clamp(playerCardScale, 55, 190);
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
        p.setProperty("trailMode", Integer.toString(trailMode));
        p.setProperty("accentColorIndex", Integer.toString(accentColorIndex));
        p.setProperty("uiStyle", Integer.toString(uiStyle));
        p.setProperty("menuSize", Integer.toString(menuSize));
        p.setProperty("hudInfoX", Integer.toString(hudInfoX));
        p.setProperty("hudInfoY", Integer.toString(hudInfoY));
        p.setProperty("hudInfoScale", Integer.toString(hudInfoScale));
        p.setProperty("playerCardX", Integer.toString(playerCardX));
        p.setProperty("playerCardY", Integer.toString(playerCardY));
        p.setProperty("playerCardScale", Integer.toString(playerCardScale));
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

    private static int clamp(int value, int min, int max) {
        return Math.max(min, Math.min(max, value));
    }
}
