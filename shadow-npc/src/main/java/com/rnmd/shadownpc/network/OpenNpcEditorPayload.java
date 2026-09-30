package com.rnmd.shadownpc.network;

import com.rnmd.shadownpc.ShadowNpcMod;
import net.minecraft.network.FriendlyByteBuf;
import net.minecraft.network.codec.StreamCodec;
import net.minecraft.network.protocol.common.custom.CustomPacketPayload;
import net.minecraft.resources.Identifier;

public record OpenNpcEditorPayload(
        int entityId,
        String name,
        String dialog,
        boolean showName,
        boolean invulnerable,
        boolean glowing,
        boolean baby,
        boolean lookAtPlayer
) implements CustomPacketPayload {
    public static final Type<OpenNpcEditorPayload> TYPE =
            new Type<>(Identifier.fromNamespaceAndPath(ShadowNpcMod.MOD_ID, "open_editor"));

    public static final StreamCodec<FriendlyByteBuf, OpenNpcEditorPayload> CODEC =
            CustomPacketPayload.codec(
                    (payload, buf) -> {
                        buf.writeVarInt(payload.entityId());
                        buf.writeUtf(payload.name(), 48);
                        buf.writeUtf(payload.dialog(), 180);
                        buf.writeBoolean(payload.showName());
                        buf.writeBoolean(payload.invulnerable());
                        buf.writeBoolean(payload.glowing());
                        buf.writeBoolean(payload.baby());
                        buf.writeBoolean(payload.lookAtPlayer());
                    },
                    buf -> new OpenNpcEditorPayload(
                            buf.readVarInt(),
                            buf.readUtf(48),
                            buf.readUtf(180),
                            buf.readBoolean(),
                            buf.readBoolean(),
                            buf.readBoolean(),
                            buf.readBoolean(),
                            buf.readBoolean()
                    )
            );

    @Override
    public Type<? extends CustomPacketPayload> type() {
        return TYPE;
    }
}
