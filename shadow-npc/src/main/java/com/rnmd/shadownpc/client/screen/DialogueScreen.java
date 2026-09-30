package com.rnmd.shadownpc.client.screen;

import com.rnmd.shadownpc.NpcData;
import com.rnmd.shadownpc.network.OpenDialoguePayload;
import com.rnmd.shadownpc.network.SelectDialoguePayload;
import net.fabricmc.fabric.api.client.networking.v1.ClientPlayNetworking;
import net.minecraft.client.gui.GuiGraphics;
import net.minecraft.client.gui.components.Button;
import net.minecraft.client.gui.screens.Screen;
import net.minecraft.network.chat.Component;

import java.util.ArrayList;
import java.util.List;

public final class DialogueScreen extends Screen {
    private final OpenDialoguePayload data;
    private final List<NpcData.DialogueChoice> choices;
    private final List<Button> choiceButtons = new ArrayList<>();

    private int selectedIndex = -1;

    public DialogueScreen(OpenDialoguePayload data) {
        super(Component.literal(data.npcName()));
        this.data = data;
        this.choices = NpcData.decodeChoices(data.choices());
    }

    private int panelWidth() { return 300; }
    private int panelHeight() { return Math.min(270, 116 + this.choices.size() * 24); }
    private int left() { return (this.width - panelWidth()) / 2; }
    private int top() { return Math.max(8, (this.height - panelHeight()) / 2); }

    @Override
    protected void init() {
        this.choiceButtons.clear();

        int l = left();
        int t = top();
        int y = t + 72;

        for (int i = 0; i < this.choices.size(); i++) {
            final int index = i;
            NpcData.DialogueChoice choice = this.choices.get(i);

            Button button = this.addRenderableWidget(Button.builder(
                    Component.literal(choice.answer()),
                    b -> choose(index)
            ).bounds(l + 14, y, panelWidth() - 28, 20).build());

            this.choiceButtons.add(button);
            y += 24;
        }

        this.addRenderableWidget(Button.builder(Component.literal("Закрыть"), b -> onClose())
                .bounds(l + 100, t + panelHeight() - 28, 100, 20).build());
    }

    private void choose(int index) {
        if (this.selectedIndex >= 0 || index < 0 || index >= this.choices.size()) return;

        this.selectedIndex = index;
        for (Button button : this.choiceButtons) {
            button.visible = false;
            button.active = false;
        }

        ClientPlayNetworking.send(new SelectDialoguePayload(this.data.entityId(), index));
    }

    @Override
    public void onClose() {
        if (this.minecraft != null) this.minecraft.setScreen(null);
    }

    @Override
    public void renderBackground(GuiGraphics graphics, int mouseX, int mouseY, float partialTick) {
        graphics.fill(0, 0, this.width, this.height, 0xA0000000);
        int l = left();
        int t = top();
        graphics.fill(l, t, l + panelWidth(), t + panelHeight(), 0xF0141820);
        graphics.fill(l, t, l + panelWidth(), t + 2, 0xFF3BA7FF);
    }

    @Override
    public void render(GuiGraphics graphics, int mouseX, int mouseY, float partialTick) {
        super.render(graphics, mouseX, mouseY, partialTick);

        int l = left();
        int t = top();

        graphics.drawCenteredString(this.font, this.data.npcName(), this.width / 2, t + 12, 0xFFFFFFFF);
        graphics.drawWordWrap(
                this.font,
                Component.literal(this.data.dialog()),
                l + 14,
                t + 34,
                panelWidth() - 28,
                0xFFE3EDF7
        );

        if (this.selectedIndex >= 0) {
            NpcData.DialogueChoice selected = this.choices.get(this.selectedIndex);
            graphics.drawWordWrap(
                    this.font,
                    Component.literal("Ты: " + selected.answer()),
                    l + 14,
                    t + 76,
                    panelWidth() - 28,
                    0xFF84F0A8
            );

            if (!selected.reply().isBlank()) {
                graphics.drawWordWrap(
                        this.font,
                        Component.literal(this.data.npcName() + ": " + selected.reply()),
                        l + 14,
                        t + 108,
                        panelWidth() - 28,
                        0xFFFFE08A
                );
            }

            if (!selected.itemId().isBlank()) {
                graphics.drawString(
                        this.font,
                        "Предмет: " + selected.itemId(),
                        l + 14,
                        t + panelHeight() - 42,
                        0xFF8EA2B8,
                        false
                );
            }
        }
    }
}
