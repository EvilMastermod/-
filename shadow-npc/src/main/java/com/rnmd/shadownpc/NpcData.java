package com.rnmd.shadownpc;

import net.minecraft.world.entity.Entity;

import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.Base64;
import java.util.Comparator;
import java.util.List;

public final class NpcData {
    public static final String NPC_TAG = "shadow_npc";
    private static final String DIALOG_PREFIX = "shadow_npc_dialog_";
    private static final String ANSWER_PREFIX = "shadow_npc_answer_";
    private static final String CHOICE_PREFIX = "shadow_npc_choice_";
    private static final String SKIN_PREFIX = "shadow_npc_skin_";
    private static final String LOOK_TAG = "shadow_npc_look_player";

    public static final String DEFAULT_DIALOG = "Привет! Что тебе нужно?";
    public static final String DEFAULT_ANSWER = "Привет!";
    public static final String DEFAULT_SKIN = "plains";
    public static final int MAX_CHOICES = 6;

    private static final int MAX_TEXT_LENGTH = 120;
    private static final int MAX_ITEM_ID_LENGTH = 96;

    public record DialogueChoice(String answer, String reply, String itemId) {
    }

    private record IndexedChoice(int index, DialogueChoice choice) {
    }

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
        replaceEncodedTag(entity, DIALOG_PREFIX, sanitizeText(text, DEFAULT_DIALOG));
    }

    public static String getDialog(Entity entity) {
        return readEncodedTag(entity, DIALOG_PREFIX, DEFAULT_DIALOG);
    }

    public static void setAnswer(Entity entity, String text) {
        replaceEncodedTag(entity, ANSWER_PREFIX, sanitizeText(text, DEFAULT_ANSWER));
    }

    public static String getAnswer(Entity entity) {
        return readEncodedTag(entity, ANSWER_PREFIX, DEFAULT_ANSWER);
    }

    public static void setChoices(Entity entity, List<DialogueChoice> choices) {
        for (String tag : new ArrayList<>(entity.getTags())) {
            if (tag.startsWith(CHOICE_PREFIX)) {
                entity.removeTag(tag);
            }
        }

        List<DialogueChoice> clean = sanitizeChoices(choices);
        for (int i = 0; i < clean.size(); i++) {
            DialogueChoice choice = clean.get(i);
            String value = i + "_" + encode(choice.answer()) + "." + encode(choice.reply()) + "." + encode(choice.itemId());
            entity.addTag(CHOICE_PREFIX + value);
        }

        setAnswer(entity, clean.getFirst().answer());
    }

    public static List<DialogueChoice> getChoices(Entity entity) {
        List<IndexedChoice> found = new ArrayList<>();

        for (String tag : entity.getTags()) {
            if (!tag.startsWith(CHOICE_PREFIX)) continue;
            String raw = tag.substring(CHOICE_PREFIX.length());
            int underscore = raw.indexOf('_');
            if (underscore <= 0) continue;

            try {
                int index = Integer.parseInt(raw.substring(0, underscore));
                String[] parts = raw.substring(underscore + 1).split("\\.", -1);
                if (parts.length != 3) continue;

                DialogueChoice choice = new DialogueChoice(
                        sanitizeText(decode(parts[0]), DEFAULT_ANSWER),
                        sanitizeTextAllowEmpty(decode(parts[1])),
                        sanitizeItemId(decode(parts[2]))
                );
                found.add(new IndexedChoice(index, choice));
            } catch (RuntimeException ignored) {
            }
        }

        if (found.isEmpty()) {
            return List.of(new DialogueChoice(getAnswer(entity), "", ""));
        }

        found.sort(Comparator.comparingInt(IndexedChoice::index));
        List<DialogueChoice> result = new ArrayList<>();
        for (IndexedChoice indexed : found) {
            if (result.size() >= MAX_CHOICES) break;
            result.add(indexed.choice());
        }
        return result;
    }

    public static String encodeChoices(List<DialogueChoice> choices) {
        List<DialogueChoice> clean = sanitizeChoices(choices);
        StringBuilder result = new StringBuilder();

        for (int i = 0; i < clean.size(); i++) {
            if (i > 0) result.append('|');
            DialogueChoice choice = clean.get(i);
            result.append(encode(choice.answer()))
                    .append('.')
                    .append(encode(choice.reply()))
                    .append('.')
                    .append(encode(choice.itemId()));
        }
        return result.toString();
    }

    public static List<DialogueChoice> decodeChoices(String data) {
        if (data == null || data.isBlank()) {
            return List.of(new DialogueChoice(DEFAULT_ANSWER, "", ""));
        }

        List<DialogueChoice> result = new ArrayList<>();
        String[] rows = data.split("\\|", -1);

        for (String row : rows) {
            if (result.size() >= MAX_CHOICES) break;
            String[] parts = row.split("\\.", -1);
            if (parts.length != 3) continue;

            try {
                result.add(new DialogueChoice(
                        sanitizeText(decode(parts[0]), DEFAULT_ANSWER),
                        sanitizeTextAllowEmpty(decode(parts[1])),
                        sanitizeItemId(decode(parts[2]))
                ));
            } catch (RuntimeException ignored) {
            }
        }

        if (result.isEmpty()) {
            result.add(new DialogueChoice(DEFAULT_ANSWER, "", ""));
        }
        return result;
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

    private static List<DialogueChoice> sanitizeChoices(List<DialogueChoice> choices) {
        List<DialogueChoice> result = new ArrayList<>();
        if (choices != null) {
            for (DialogueChoice choice : choices) {
                if (choice == null) continue;
                result.add(new DialogueChoice(
                        sanitizeText(choice.answer(), DEFAULT_ANSWER),
                        sanitizeTextAllowEmpty(choice.reply()),
                        sanitizeItemId(choice.itemId())
                ));
                if (result.size() >= MAX_CHOICES) break;
            }
        }

        if (result.isEmpty()) {
            result.add(new DialogueChoice(DEFAULT_ANSWER, "", ""));
        }
        return result;
    }

    private static String sanitizeText(String text, String fallback) {
        String clean = text == null ? "" : text.strip();
        if (clean.isEmpty()) clean = fallback;
        if (clean.length() > MAX_TEXT_LENGTH) clean = clean.substring(0, MAX_TEXT_LENGTH);
        return clean;
    }

    private static String sanitizeTextAllowEmpty(String text) {
        String clean = text == null ? "" : text.strip();
        if (clean.length() > MAX_TEXT_LENGTH) clean = clean.substring(0, MAX_TEXT_LENGTH);
        return clean;
    }

    private static String sanitizeItemId(String text) {
        String clean = text == null ? "" : text.strip().toLowerCase();
        if (clean.length() > MAX_ITEM_ID_LENGTH) clean = clean.substring(0, MAX_ITEM_ID_LENGTH);
        return clean;
    }

    private static void replaceEncodedTag(Entity entity, String prefix, String value) {
        for (String tag : new ArrayList<>(entity.getTags())) {
            if (tag.startsWith(prefix)) {
                entity.removeTag(tag);
            }
        }
        entity.addTag(prefix + encode(value));
    }

    private static String readEncodedTag(Entity entity, String prefix, String fallback) {
        for (String tag : entity.getTags()) {
            if (!tag.startsWith(prefix)) continue;
            try {
                String decoded = decode(tag.substring(prefix.length())).strip();
                return decoded.isEmpty() ? fallback : decoded;
            } catch (IllegalArgumentException ignored) {
                return fallback;
            }
        }
        return fallback;
    }

    private static String encode(String value) {
        return Base64.getUrlEncoder()
                .withoutPadding()
                .encodeToString(value.getBytes(StandardCharsets.UTF_8));
    }

    private static String decode(String value) {
        if (value.isEmpty()) return "";
        return new String(Base64.getUrlDecoder().decode(value), StandardCharsets.UTF_8);
    }
}
