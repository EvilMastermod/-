package com.rnmd.shadownpc.network;

import com.rnmd.shadownpc.ShadowNpcMod;
import net.minecraft.network.FriendlyByteBuf;
import net.minecraft.network.codec.StreamCodec;
import net.minecraft.network.protocol.common.custom.CustomPacketPayload;
import net.minecraft.resources.Identifier;

public record OpenNpcEditorPayload(
        int entityId,
        String name,
        String skin,
        String dialog,
        String choices,
        boolean showName,
        boolean invulnerable
) implements CustomPacketPayload {
    public static final Type<OpenNpcEditorPayload> TYPE =
            new Type<>(Identifier.fromNamespaceAndPath(ShadowNpcMod.MOD_ID, "open_editor"));

    public static final StreamCodec<FriendlyByteBuf, OpenNpcEditorPayload> CODEC =
            CustomPacketPayload.codec(
                    (payload, buf) -> {
                        buf.writeVarInt(payload.entityId());
                        buf.writeUtf(payload.name(), 48);
                        buf.writeUtf(payload.skin(), 24);
                        buf.writeUtf(payload.dialog(), 180);
                        buf.writeUtf(payload.choices(), 4096);
                        buf.writeBoolean(payload.showName());
                        buf.writeBoolean(payload.invulnerable());
                    },
                    buf -> new OpenNpcEditorPayload(
                            buf.readVarInt(),
                            buf.readUtf(48),
                            buf.readUtf(24),
                            buf.readUtf(180),
                            buf.readUtf(4096),
                            buf.readBoolean(),
                            buf.readBoolean()
                    )
            );

    @Override
    public Type<? extends CustomPacketPayload> type() {
        return TYPE;
    }
}
