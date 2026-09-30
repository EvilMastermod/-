package com.rnmd.shadownpc.network;

import com.rnmd.shadownpc.ShadowNpcMod;
import net.minecraft.network.FriendlyByteBuf;
import net.minecraft.network.codec.StreamCodec;
import net.minecraft.network.protocol.common.custom.CustomPacketPayload;
import net.minecraft.resources.Identifier;

public record OpenDialoguePayload(
        int entityId,
        String npcName,
        String dialog,
        String choices
) implements CustomPacketPayload {
    public static final Type<OpenDialoguePayload> TYPE =
            new Type<>(Identifier.fromNamespaceAndPath(ShadowNpcMod.MOD_ID, "open_dialogue"));

    public static final StreamCodec<FriendlyByteBuf, OpenDialoguePayload> CODEC =
            CustomPacketPayload.codec(
                    (payload, buf) -> {
                        buf.writeVarInt(payload.entityId());
                        buf.writeUtf(payload.npcName(), 48);
                        buf.writeUtf(payload.dialog(), 180);
                        buf.writeUtf(payload.choices(), 4096);
                    },
                    buf -> new OpenDialoguePayload(
                            buf.readVarInt(),
                            buf.readUtf(48),
                            buf.readUtf(180),
                            buf.readUtf(4096)
                    )
            );

    @Override
    public Type<? extends CustomPacketPayload> type() {
        return TYPE;
    }
}
