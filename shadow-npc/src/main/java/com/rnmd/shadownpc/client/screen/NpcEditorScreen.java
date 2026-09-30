package com.rnmd.shadownpc.client.screen;

import com.rnmd.shadownpc.network.OpenNpcEditorPayload;
import com.rnmd.shadownpc.network.SaveNpcPayload;
import net.fabricmc.fabric.api.client.networking.v1.ClientPlayNetworking;
import net.minecraft.client.gui.GuiGraphics;
import net.minecraft.client.gui.components.Button;
import net.minecraft.client.gui.components.EditBox;
import net.minecraft.client.gui.screens.Screen;
import net.minecraft.network.chat.Component;

public final class NpcEditorScreen extends Screen {
    private static final String[] SKINS = {"plains", "desert", "jungle", "savanna", "snow", "swamp", "taiga"};
    private static final String[] SKIN_NAMES = {"Обычный", "Пустыня", "Джунгли", "Саванна", "Снег", "Болото", "Тайга"};

    private enum Tab { NAME_SKIN, DIALOGS }

    private final OpenNpcEditorPayload data;
    private Tab tab = Tab.NAME_SKIN;

    private EditBox nameBox;
    private EditBox dialogBox;
    private EditBox answerBox;

    private Button nameTabButton;
    private Button dialogTabButton;
    private Button skinButton;
    private Button showNameButton;
    private Button invulnerableButton;

    private int skinIndex;
    private boolean showName;
    private boolean invulnerable;

    public NpcEditorScreen(OpenNpcEditorPayload data) {
        super(Component.literal("Редактор NPC"));
        this.data = data;
        this.skinIndex = findSkin(data.skin());
        this.showName = data.showName();
        this.invulnerable = data.invulnerable();
    }

    private int panelWidth() { return 270; }
    private int panelHeight() { return 186; }
    private int left() { return (this.width - panelWidth()) / 2; }
    private int top() { return Math.max(8, (this.height - panelHeight()) / 2); }

    @Override
    protected void init() {
        int l = left();
        int t = top();
        int fieldWidth = panelWidth() - 24;

        this.nameTabButton = this.addRenderableWidget(Button.builder(Component.literal("Название и скин"), b -> {
            this.tab = Tab.NAME_SKIN;
            refreshTab();
        }).bounds(l + 12, t + 10, 120, 20).build());

        this.dialogTabButton = this.addRenderableWidget(Button.builder(Component.literal("Диалоги"), b -> {
            this.tab = Tab.DIALOGS;
            refreshTab();
        }).bounds(l + 138, t + 10, 120, 20).build());

        this.nameBox = this.addRenderableWidget(new EditBox(this.font, l + 12, t + 57, fieldWidth, 20, Component.literal("Название")));
        this.nameBox.setMaxLength(48);
        this.nameBox.setValue(this.data.name());

        this.skinButton = this.addRenderableWidget(Button.builder(Component.empty(), b -> {
            this.skinIndex = (this.skinIndex + 1) % SKINS.length;
            refreshSkinButton();
        }).bounds(l + 12, t + 88, fieldWidth, 20).build());

        this.showNameButton = this.addRenderableWidget(Button.builder(Component.empty(), b -> {
            this.showName = !this.showName;
            refreshToggleButtons();
        }).bounds(l + 12, t + 114, 120, 20).build());

        this.invulnerableButton = this.addRenderableWidget(Button.builder(Component.empty(), b -> {
            this.invulnerable = !this.invulnerable;
            refreshToggleButtons();
        }).bounds(l + 138, t + 114, 120, 20).build());

        this.dialogBox = this.addRenderableWidget(new EditBox(this.font, l + 12, t + 57, fieldWidth, 20, Component.literal("Фраза NPC")));
        this.dialogBox.setMaxLength(180);
        this.dialogBox.setValue(this.data.dialog());

        this.answerBox = this.addRenderableWidget(new EditBox(this.font, l + 12, t + 101, fieldWidth, 20, Component.literal("Ответ игрока")));
        this.answerBox.setMaxLength(180);
        this.answerBox.setValue(this.data.answer());

        int footerY = t + panelHeight() - 28;
        this.addRenderableWidget(Button.builder(Component.literal("Сохранить"), b -> save())
                .bounds(l + 12, footerY, 78, 20).build());
        this.addRenderableWidget(Button.builder(Component.literal("Удалить"), b -> deleteNpc())
                .bounds(l + 96, footerY, 78, 20).build());
        this.addRenderableWidget(Button.builder(Component.literal("Отмена"), b -> closeScreen())
                .bounds(l + 180, footerY, 78, 20).build());

        refreshSkinButton();
        refreshToggleButtons();
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
    }

    private void save() {
        ClientPlayNetworking.send(new SaveNpcPayload(
                this.data.entityId(),
                this.nameBox.getValue(),
                SKINS[this.skinIndex],
                this.dialogBox.getValue(),
                this.answerBox.getValue(),
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
                this.answerBox.getValue(),
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
            graphics.drawString(this.font, "Название", l + 12, t + 47, 0xFFB9CBE0, false);
            graphics.drawString(this.font, "Нажимай на кнопку скина для выбора", l + 12, t + 79, 0xFF78899B, false);
        } else {
            graphics.drawString(this.font, "Что говорит NPC", l + 12, t + 47, 0xFFB9CBE0, false);
            graphics.drawString(this.font, "Кнопка-ответ игрока", l + 12, t + 91, 0xFFB9CBE0, false);
        }
    }
}
