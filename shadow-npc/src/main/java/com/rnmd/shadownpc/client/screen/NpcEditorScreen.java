package com.rnmd.shadownpc.client.screen;

import com.rnmd.shadownpc.NpcData;
import com.rnmd.shadownpc.network.OpenNpcEditorPayload;
import com.rnmd.shadownpc.network.SaveNpcPayload;
import net.fabricmc.fabric.api.client.networking.v1.ClientPlayNetworking;
import net.minecraft.client.gui.GuiGraphics;
import net.minecraft.client.gui.components.Button;
import net.minecraft.client.gui.components.EditBox;
import net.minecraft.client.gui.screens.Screen;
import net.minecraft.network.chat.Component;

import java.util.ArrayList;
import java.util.List;

public final class NpcEditorScreen extends Screen {
    private static final String[] SKINS = {"plains", "desert", "jungle", "savanna", "snow", "swamp", "taiga"};
    private static final String[] SKIN_NAMES = {"Обычный", "Пустыня", "Джунгли", "Саванна", "Снег", "Болото", "Тайга"};

    private enum Tab { NAME_SKIN, DIALOGS }

    private static final class ChoiceDraft {
        String answer;
        String reply;
        String itemId;

        ChoiceDraft(String answer, String reply, String itemId) {
            this.answer = answer;
            this.reply = reply;
            this.itemId = itemId;
        }
    }

    private final OpenNpcEditorPayload data;
    private final List<ChoiceDraft> choices = new ArrayList<>();

    private Tab tab = Tab.NAME_SKIN;
    private int choiceIndex;
    private int skinIndex;
    private boolean showName;
    private boolean invulnerable;

    private EditBox nameBox;
    private EditBox dialogBox;
    private EditBox answerBox;
    private EditBox replyBox;
    private EditBox itemBox;

    private Button nameTabButton;
    private Button dialogTabButton;
    private Button skinButton;
    private Button showNameButton;
    private Button invulnerableButton;
    private Button prevButton;
    private Button nextButton;
    private Button addChoiceButton;
    private Button removeChoiceButton;

    public NpcEditorScreen(OpenNpcEditorPayload data) {
        super(Component.literal("Редактор NPC"));
        this.data = data;
        this.skinIndex = findSkin(data.skin());
        this.showName = data.showName();
        this.invulnerable = data.invulnerable();

        for (NpcData.DialogueChoice choice : NpcData.decodeChoices(data.choices())) {
            this.choices.add(new ChoiceDraft(choice.answer(), choice.reply(), choice.itemId()));
        }
        if (this.choices.isEmpty()) {
            this.choices.add(new ChoiceDraft(NpcData.DEFAULT_ANSWER, "", ""));
        }
    }

    private int panelWidth() { return 310; }
    private int panelHeight() { return 252; }
    private int left() { return (this.width - panelWidth()) / 2; }
    private int top() { return Math.max(6, (this.height - panelHeight()) / 2); }

    @Override
    protected void init() {
        int l = left();
        int t = top();
        int fieldWidth = panelWidth() - 24;

        this.nameTabButton = this.addRenderableWidget(Button.builder(Component.literal("Название и скин"), b -> {
            saveCurrentChoiceFields();
            this.tab = Tab.NAME_SKIN;
            refreshTab();
        }).bounds(l + 12, t + 10, 136, 20).build());

        this.dialogTabButton = this.addRenderableWidget(Button.builder(Component.literal("Диалоги"), b -> {
            this.tab = Tab.DIALOGS;
            refreshTab();
            loadCurrentChoiceFields();
        }).bounds(l + 162, t + 10, 136, 20).build());

        this.nameBox = this.addRenderableWidget(new EditBox(this.font, l + 12, t + 58, fieldWidth, 20, Component.literal("Название")));
        this.nameBox.setMaxLength(48);
        this.nameBox.setValue(this.data.name());

        this.skinButton = this.addRenderableWidget(Button.builder(Component.empty(), b -> {
            this.skinIndex = (this.skinIndex + 1) % SKINS.length;
            refreshSkinButton();
        }).bounds(l + 12, t + 92, fieldWidth, 20).build());

        this.showNameButton = this.addRenderableWidget(Button.builder(Component.empty(), b -> {
            this.showName = !this.showName;
            refreshToggleButtons();
        }).bounds(l + 12, t + 120, 136, 20).build());

        this.invulnerableButton = this.addRenderableWidget(Button.builder(Component.empty(), b -> {
            this.invulnerable = !this.invulnerable;
            refreshToggleButtons();
        }).bounds(l + 162, t + 120, 136, 20).build());

        this.dialogBox = this.addRenderableWidget(new EditBox(this.font, l + 12, t + 58, fieldWidth, 20, Component.literal("Начальный текст NPC")));
        this.dialogBox.setMaxLength(120);
        this.dialogBox.setValue(this.data.dialog());

        this.answerBox = this.addRenderableWidget(new EditBox(this.font, l + 12, t + 92, fieldWidth, 20, Component.literal("Текст кнопки")));
        this.answerBox.setMaxLength(120);

        this.replyBox = this.addRenderableWidget(new EditBox(this.font, l + 12, t + 126, fieldWidth, 20, Component.literal("Ответ NPC")));
        this.replyBox.setMaxLength(120);

        this.itemBox = this.addRenderableWidget(new EditBox(this.font, l + 12, t + 160, fieldWidth, 20, Component.literal("Предмет")));
        this.itemBox.setMaxLength(96);
        this.itemBox.setHint(Component.literal("minecraft:diamond"));

        int navY = t + 190;
        this.prevButton = this.addRenderableWidget(Button.builder(Component.literal("<"), b -> switchChoice(-1))
                .bounds(l + 12, navY, 34, 20).build());

        this.addChoiceButton = this.addRenderableWidget(Button.builder(Component.literal("+ Ещё диалог"), b -> addChoice())
                .bounds(l + 52, navY, 112, 20).build());

        this.nextButton = this.addRenderableWidget(Button.builder(Component.literal(">"), b -> switchChoice(1))
                .bounds(l + 170, navY, 34, 20).build());

        this.removeChoiceButton = this.addRenderableWidget(Button.builder(Component.literal("Удалить"), b -> removeChoice())
                .bounds(l + 210, navY, 88, 20).build());

        int footerY = t + panelHeight() - 28;
        this.addRenderableWidget(Button.builder(Component.literal("Сохранить"), b -> save())
                .bounds(l + 12, footerY, 88, 20).build());
        this.addRenderableWidget(Button.builder(Component.literal("Удалить NPC"), b -> deleteNpc())
                .bounds(l + 106, footerY, 96, 20).build());
        this.addRenderableWidget(Button.builder(Component.literal("Отмена"), b -> closeScreen())
                .bounds(l + 208, footerY, 90, 20).build());

        refreshSkinButton();
        refreshToggleButtons();
        loadCurrentChoiceFields();
        refreshTab();
    }

    private int findSkin(String skin) {
        for (int i = 0; i < SKINS.length; i++) {
            if (SKINS[i].equalsIgnoreCase(skin)) return i;
        }
        return 0;
    }

    private void refreshSkinButton() {
        if (this.skinButton != null) {
            this.skinButton.setMessage(Component.literal("Скин: " + SKIN_NAMES[this.skinIndex]));
        }
    }

    private void refreshToggleButtons() {
        if (this.showNameButton != null) {
            this.showNameButton.setMessage(Component.literal((this.showName ? "§a" : "§c") + "Имя: " + (this.showName ? "Вкл" : "Выкл")));
        }
        if (this.invulnerableButton != null) {
            this.invulnerableButton.setMessage(Component.literal((this.invulnerable ? "§a" : "§c") + "Неуязвим"));
        }
    }

    private void refreshTab() {
        boolean nameTab = this.tab == Tab.NAME_SKIN;

        this.nameTabButton.active = !nameTab;
        this.dialogTabButton.active = nameTab;

        this.nameBox.visible = nameTab;
        this.nameBox.setEditable(nameTab);
        this.skinButton.visible = nameTab;
        this.skinButton.active = nameTab;
        this.showNameButton.visible = nameTab;
        this.showNameButton.active = nameTab;
        this.invulnerableButton.visible = nameTab;
        this.invulnerableButton.active = nameTab;

        this.dialogBox.visible = !nameTab;
        this.dialogBox.setEditable(!nameTab);
        this.answerBox.visible = !nameTab;
        this.answerBox.setEditable(!nameTab);
        this.replyBox.visible = !nameTab;
        this.replyBox.setEditable(!nameTab);
        this.itemBox.visible = !nameTab;
        this.itemBox.setEditable(!nameTab);

        this.prevButton.visible = !nameTab;
        this.prevButton.active = !nameTab && this.choiceIndex > 0;
        this.nextButton.visible = !nameTab;
        this.nextButton.active = !nameTab && this.choiceIndex < this.choices.size() - 1;
        this.addChoiceButton.visible = !nameTab;
        this.addChoiceButton.active = !nameTab && this.choices.size() < NpcData.MAX_CHOICES;
        this.removeChoiceButton.visible = !nameTab;
        this.removeChoiceButton.active = !nameTab && this.choices.size() > 1;
    }

    private void saveCurrentChoiceFields() {
        if (this.answerBox == null || this.choices.isEmpty()) return;
        ChoiceDraft current = this.choices.get(this.choiceIndex);
        current.answer = this.answerBox.getValue();
        current.reply = this.replyBox.getValue();
        current.itemId = this.itemBox.getValue();
    }

    private void loadCurrentChoiceFields() {
        if (this.answerBox == null || this.choices.isEmpty()) return;
        ChoiceDraft current = this.choices.get(this.choiceIndex);
        this.answerBox.setValue(current.answer);
        this.replyBox.setValue(current.reply);
        this.itemBox.setValue(current.itemId);
        refreshTab();
    }

    private void switchChoice(int direction) {
        saveCurrentChoiceFields();
        this.choiceIndex = Math.max(0, Math.min(this.choices.size() - 1, this.choiceIndex + direction));
        loadCurrentChoiceFields();
    }

    private void addChoice() {
        if (this.choices.size() >= NpcData.MAX_CHOICES) return;
        saveCurrentChoiceFields();
        this.choices.add(new ChoiceDraft("Ответ " + (this.choices.size() + 1), "", ""));
        this.choiceIndex = this.choices.size() - 1;
        loadCurrentChoiceFields();
    }

    private void removeChoice() {
        if (this.choices.size() <= 1) return;
        this.choices.remove(this.choiceIndex);
        if (this.choiceIndex >= this.choices.size()) this.choiceIndex = this.choices.size() - 1;
        loadCurrentChoiceFields();
    }

    private String encodedChoices() {
        saveCurrentChoiceFields();
        List<NpcData.DialogueChoice> result = new ArrayList<>();
        for (ChoiceDraft draft : this.choices) {
            result.add(new NpcData.DialogueChoice(draft.answer, draft.reply, draft.itemId));
        }
        return NpcData.encodeChoices(result);
    }

    private void save() {
        ClientPlayNetworking.send(new SaveNpcPayload(
                this.data.entityId(),
                this.nameBox.getValue(),
                SKINS[this.skinIndex],
                this.dialogBox.getValue(),
                encodedChoices(),
                this.showName,
                this.invulnerable,
                false
        ));
        closeScreen();
    }

    private void deleteNpc() {
        ClientPlayNetworking.send(new SaveNpcPayload(
                this.data.entityId(),
                this.nameBox.getValue(),
                SKINS[this.skinIndex],
                this.dialogBox.getValue(),
                encodedChoices(),
                this.showName,
                this.invulnerable,
                true
        ));
        closeScreen();
    }

    private void closeScreen() {
        if (this.minecraft != null) this.minecraft.setScreen(null);
    }

    @Override
    public void onClose() {
        closeScreen();
    }

    @Override
    public void renderBackground(GuiGraphics graphics, int mouseX, int mouseY, float partialTick) {
        graphics.fill(0, 0, this.width, this.height, 0xA0000000);
        int l = left();
        int t = top();
        int r = l + panelWidth();
        int b = t + panelHeight();
        graphics.fill(l, t, r, b, 0xF0141820);
        graphics.fill(l, t, r, t + 2, 0xFF3BA7FF);
    }

    @Override
    public void render(GuiGraphics graphics, int mouseX, int mouseY, float partialTick) {
        super.render(graphics, mouseX, mouseY, partialTick);
        int l = left();
        int t = top();

        graphics.drawCenteredString(this.font, this.title, this.width / 2, t + 36, 0xFFFFFFFF);

        if (this.tab == Tab.NAME_SKIN) {
            graphics.drawString(this.font, "Название", l + 12, t + 48, 0xFFB9CBE0, false);
            graphics.drawString(this.font, "Внешность NPC", l + 12, t + 82, 0xFFB9CBE0, false);
        } else {
            graphics.drawString(this.font, "Начальная фраза NPC", l + 12, t + 48, 0xFFB9CBE0, false);
            graphics.drawString(this.font, "Кнопка / твой ответ", l + 12, t + 82, 0xFFB9CBE0, false);
            graphics.drawString(this.font, "Что NPC ответит после выбора", l + 12, t + 116, 0xFFB9CBE0, false);
            graphics.drawString(this.font, "Предмет за этот ответ", l + 12, t + 150, 0xFFB9CBE0, false);
            graphics.drawString(this.font,
                    "Диалог " + (this.choiceIndex + 1) + "/" + this.choices.size(),
                    l + 218, t + 196, 0xFF8EA2B8, false);
        }
    }
}
