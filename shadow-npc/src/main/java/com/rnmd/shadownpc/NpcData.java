package com.rnmd.shadownpc;

import net.minecraft.world.entity.Entity;

import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.Base64;

public final class NpcData {
    public static final String NPC_TAG = "shadow_npc";
    private static final String DIALOG_PREFIX = "shadow_npc_dialog_";
    private static final String LOOK_TAG = "shadow_npc_look_player";
    public static final String DEFAULT_DIALOG = "Привет! Я NPC.";
    private static final int MAX_DIALOG_LENGTH = 180;

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
        for (String tag : new ArrayList<>(entity.getTags())) {
            if (tag.startsWith(DIALOG_PREFIX)) {
                entity.removeTag(tag);
            }
        }

        String clean = text == null ? "" : text.strip();
        if (clean.isEmpty()) {
            clean = DEFAULT_DIALOG;
        }
        if (clean.length() > MAX_DIALOG_LENGTH) {
            clean = clean.substring(0, MAX_DIALOG_LENGTH);
        }

        String encoded = Base64.getUrlEncoder()
                .withoutPadding()
                .encodeToString(clean.getBytes(StandardCharsets.UTF_8));
        entity.addTag(DIALOG_PREFIX + encoded);
    }

    public static String getDialog(Entity entity) {
        for (String tag : entity.getTags()) {
            if (!tag.startsWith(DIALOG_PREFIX)) continue;
            try {
                String encoded = tag.substring(DIALOG_PREFIX.length());
                byte[] bytes = Base64.getUrlDecoder().decode(encoded);
                String decoded = new String(bytes, StandardCharsets.UTF_8).strip();
                return decoded.isEmpty() ? DEFAULT_DIALOG : decoded;
            } catch (IllegalArgumentException ignored) {
                return DEFAULT_DIALOG;
            }
        }
        return DEFAULT_DIALOG;
    }
}
