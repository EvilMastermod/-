package com.rnmd.shadownpc;

import net.minecraft.world.entity.Entity;

import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.Base64;

public final class NpcData {
    public static final String NPC_TAG = "shadow_npc";
    private static final String DIALOG_PREFIX = "shadow_npc_dialog_";
    private static final String ANSWER_PREFIX = "shadow_npc_answer_";
    private static final String SKIN_PREFIX = "shadow_npc_skin_";
    private static final String LOOK_TAG = "shadow_npc_look_player";

    public static final String DEFAULT_DIALOG = "Привет! Я NPC.";
    public static final String DEFAULT_ANSWER = "Привет!";
    public static final String DEFAULT_SKIN = "plains";
    private static final int MAX_TEXT_LENGTH = 180;

    private NpcData() {
    }

    public static boolean isNpc(Entity entity) {
        return entity.getTags().contains(NPC_TAG);
    }

    public static void markNpc(Entity entity) {
        entity.addTag(NPC_TAG);
    }

    public static void setLookAtPlayer(Entity entity, boolean enabled) {
        if (enabled) entity.addTag(LOOK_TAG);
        else entity.removeTag(LOOK_TAG);
    }

    public static boolean shouldLookAtPlayer(Entity entity) {
        return entity.getTags().contains(LOOK_TAG);
    }

    public static void setDialog(Entity entity, String text) {
        replaceEncodedTag(entity, DIALOG_PREFIX, sanitize(text, DEFAULT_DIALOG));
    }

    public static String getDialog(Entity entity) {
        return readEncodedTag(entity, DIALOG_PREFIX, DEFAULT_DIALOG);
    }

    public static void setAnswer(Entity entity, String text) {
        replaceEncodedTag(entity, ANSWER_PREFIX, sanitize(text, DEFAULT_ANSWER));
    }

    public static String getAnswer(Entity entity) {
        return readEncodedTag(entity, ANSWER_PREFIX, DEFAULT_ANSWER);
    }

    public static void setSkin(Entity entity, String skin) {
        for (String tag : new ArrayList<>(entity.getTags())) {
            if (tag.startsWith(SKIN_PREFIX)) {
                entity.removeTag(tag);
            }
        }
        String clean = skin == null ? DEFAULT_SKIN : skin.strip().toLowerCase();
        if (clean.isEmpty()) clean = DEFAULT_SKIN;
        entity.addTag(SKIN_PREFIX + clean);
    }

    public static String getSkin(Entity entity) {
        for (String tag : entity.getTags()) {
            if (tag.startsWith(SKIN_PREFIX)) {
                String value = tag.substring(SKIN_PREFIX.length()).strip().toLowerCase();
                return value.isEmpty() ? DEFAULT_SKIN : value;
            }
        }
        return DEFAULT_SKIN;
    }

    private static String sanitize(String text, String fallback) {
        String clean = text == null ? "" : text.strip();
        if (clean.isEmpty()) clean = fallback;
        if (clean.length() > MAX_TEXT_LENGTH) clean = clean.substring(0, MAX_TEXT_LENGTH);
        return clean;
    }

    private static void replaceEncodedTag(Entity entity, String prefix, String value) {
        for (String tag : new ArrayList<>(entity.getTags())) {
            if (tag.startsWith(prefix)) {
                entity.removeTag(tag);
            }
        }

        String encoded = Base64.getUrlEncoder()
                .withoutPadding()
                .encodeToString(value.getBytes(StandardCharsets.UTF_8));
        entity.addTag(prefix + encoded);
    }

    private static String readEncodedTag(Entity entity, String prefix, String fallback) {
        for (String tag : entity.getTags()) {
            if (!tag.startsWith(prefix)) continue;
            try {
                String encoded = tag.substring(prefix.length());
                byte[] bytes = Base64.getUrlDecoder().decode(encoded);
                String decoded = new String(bytes, StandardCharsets.UTF_8).strip();
                return decoded.isEmpty() ? fallback : decoded;
            } catch (IllegalArgumentException ignored) {
                return fallback;
            }
        }
        return fallback;
    }
}
