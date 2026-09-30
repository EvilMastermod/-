package com.rnmd.shadownpc.client.screen;

import com.rnmd.shadownpc.network.OpenDialoguePayload;
import net.minecraft.client.gui.GuiGraphics;
import net.minecraft.client.gui.components.Button;
import net.minecraft.client.gui.screens.Screen;
import net.minecraft.network.chat.Component;

public final class DialogueScreen extends Screen {
    private final OpenDialoguePayload data;
    private boolean answered;
    private Button answerButton;

    public DialogueScreen(OpenDialoguePayload data) {
        super(Component.literal(data.npcName()));
        this.data = data;
    }

    private int panelWidth() { return 280; }
    private int panelHeight() { return 148; }
    private int left() { return (this.width - panelWidth()) / 2; }
    private int top() { return Math.max(8, (this.height - panelHeight()) / 2); }

    @Override
    protected void init() {
        int l = left();
        int t = top();

        this.answerButton = this.addRenderableWidget(Button.builder(Component.literal(this.data.answer()), b -> {
            this.answered = true;
            b.active = false;
            b.setMessage(Component.literal("§aТы: §f" + this.data.answer()));
        }).bounds(l + 14, t + 88, panelWidth() - 28, 20).build());

        this.addRenderableWidget(Button.builder(Component.literal("Закрыть"), b -> onClose())
                .bounds(l + 90, t + 116, 100, 20).build());
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
        graphics.drawString(this.font, this.data.dialog(), l + 14, t + 40, 0xFFE3EDF7, false);

        if (this.answered) {
            graphics.drawString(this.font, "Ответ выбран", l + 14, t + 67, 0xFF84F0A8, false);
        } else {
            graphics.drawString(this.font, "Выбери ответ:", l + 14, t + 67, 0xFF91A3B5, false);
        }
    }
}
