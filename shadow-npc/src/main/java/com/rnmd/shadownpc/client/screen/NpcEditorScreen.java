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
    private final OpenNpcEditorPayload data;

    private EditBox nameBox;
    private EditBox dialogBox;

    private boolean showName;
    private boolean invulnerable;
    private boolean glowing;
    private boolean baby;
    private boolean lookAtPlayer;

    private Button showNameButton;
    private Button invulnerableButton;
    private Button glowingButton;
    private Button babyButton;
    private Button lookButton;

    public NpcEditorScreen(OpenNpcEditorPayload data) {
        super(Component.literal("Редактор NPC"));
        this.data = data;
        this.showName = data.showName();
        this.invulnerable = data.invulnerable();
        this.glowing = data.glowing();
        this.baby = data.baby();
        this.lookAtPlayer = data.lookAtPlayer();
    }

    private int panelWidth() {
        return Math.min(360, Math.max(300, this.width - 24));
    }

    private int panelHeight() {
        return Math.min(290, Math.max(255, this.height - 24));
    }

    private int left() {
        return (this.width - panelWidth()) / 2;
    }

    private int top() {
        return Math.max(12, (this.height - panelHeight()) / 2);
    }

    @Override
    protected void init() {
        int left = left();
        int top = top();
        int width = panelWidth();
        int fieldWidth = width - 32;

        this.nameBox = new EditBox(this.font, left + 16, top + 46, fieldWidth, 20, Component.literal("Название"));
        this.nameBox.setMaxLength(48);
        this.nameBox.setValue(this.data.name());
        this.nameBox.setHint(Component.literal("Название NPC"));
        this.addRenderableWidget(this.nameBox);

        this.dialogBox = new EditBox(this.font, left + 16, top + 92, fieldWidth, 20, Component.literal("Диалог"));
        this.dialogBox.setMaxLength(180);
        this.dialogBox.setValue(this.data.dialog());
        this.dialogBox.setHint(Component.literal("Что NPC говорит по ПКМ"));
        this.addRenderableWidget(this.dialogBox);

        int half = (fieldWidth - 6) / 2;
        int y = top + 128;

        this.showNameButton = addToggle(left + 16, y, half, "Имя видно", this.showName, () -> {
            this.showName = !this.showName;
            refreshToggles();
        });

        this.invulnerableButton = addToggle(left + 22 + half, y, half, "Неуязвим", this.invulnerable, () -> {
            this.invulnerable = !this.invulnerable;
            refreshToggles();
        });

        y += 24;
        this.glowingButton = addToggle(left + 16, y, half, "Свечение", this.glowing, () -> {
            this.glowing = !this.glowing;
            refreshToggles();
        });

        this.babyButton = addToggle(left + 22 + half, y, half, "Ребёнок", this.baby, () -> {
            this.baby = !this.baby;
            refreshToggles();
        });

        y += 24;
        this.lookButton = addToggle(left + 16, y, fieldWidth, "Смотреть на ближайшего игрока", this.lookAtPlayer, () -> {
            this.lookAtPlayer = !this.lookAtPlayer;
            refreshToggles();
        });

        int footerY = top + panelHeight() - 34;
        int buttonWidth = (fieldWidth - 12) / 3;

        this.addRenderableWidget(Button.builder(Component.literal("Сохранить"), button -> save())
                .bounds(left + 16, footerY, buttonWidth, 20).build());

        this.addRenderableWidget(Button.builder(Component.literal("Удалить"), button -> deleteNpc())
                .bounds(left + 22 + buttonWidth, footerY, buttonWidth, 20).build());

        this.addRenderableWidget(Button.builder(Component.literal("Отмена"), button -> closeScreen())
                .bounds(left + 28 + buttonWidth * 2, footerY, buttonWidth, 20).build());

        refreshToggles();
        this.setInitialFocus(this.nameBox);
    }

    private Button addToggle(int x, int y, int width, String label, boolean value, Runnable click) {
        Button button = Button.builder(toggleText(label, value), b -> click.run())
                .bounds(x, y, width, 20)
                .build();
        this.addRenderableWidget(button);
        return button;
    }

    private Component toggleText(String label, boolean enabled) {
        return Component.literal((enabled ? "§a[ВКЛ] §f" : "§c[ВЫКЛ] §f") + label);
    }

    private void refreshToggles() {
        if (this.showNameButton != null) this.showNameButton.setMessage(toggleText("Имя видно", this.showName));
        if (this.invulnerableButton != null) this.invulnerableButton.setMessage(toggleText("Неуязвим", this.invulnerable));
        if (this.glowingButton != null) this.glowingButton.setMessage(toggleText("Свечение", this.glowing));
        if (this.babyButton != null) this.babyButton.setMessage(toggleText("Ребёнок", this.baby));
        if (this.lookButton != null) this.lookButton.setMessage(toggleText("Смотреть на ближайшего игрока", this.lookAtPlayer));
    }

    private void save() {
        ClientPlayNetworking.send(new SaveNpcPayload(
                this.data.entityId(),
                this.nameBox.getValue(),
                this.dialogBox.getValue(),
                this.showName,
                this.invulnerable,
                this.glowing,
                this.baby,
                this.lookAtPlayer,
                false
        ));
        closeScreen();
    }

    private void deleteNpc() {
        ClientPlayNetworking.send(new SaveNpcPayload(
                this.data.entityId(),
                this.nameBox.getValue(),
                this.dialogBox.getValue(),
                this.showName,
                this.invulnerable,
                this.glowing,
                this.baby,
                this.lookAtPlayer,
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
        graphics.fill(0, 0, this.width, this.height, 0xB0000000);
        int l = left();
        int t = top();
        int r = l + panelWidth();
        int b = t + panelHeight();
        graphics.fill(l, t, r, b, 0xEE11151D);
        graphics.fill(l, t, r, t + 2, 0xFF36A8FF);
        graphics.fill(l, b - 2, r, b, 0xFF143D66);
    }

    @Override
    public void render(GuiGraphics graphics, int mouseX, int mouseY, float partialTick) {
        super.render(graphics, mouseX, mouseY, partialTick);
        int l = left();
        int t = top();
        graphics.drawCenteredString(this.font, this.title, this.width / 2, t + 14, 0xFFFFFFFF);
        graphics.drawString(this.font, "Название NPC", l + 16, t + 34, 0xFFB8C7DB, false);
        graphics.drawString(this.font, "Диалог по ПКМ", l + 16, t + 80, 0xFFB8C7DB, false);
        graphics.drawString(this.font, "NPC всегда стоит на месте", l + 16, t + 202, 0xFF78889B, false);
    }
}
