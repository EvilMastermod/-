package com.rnmd.shadownpc.client;

import com.rnmd.shadownpc.client.screen.DialogueScreen;
import com.rnmd.shadownpc.client.screen.NpcEditorScreen;
import com.rnmd.shadownpc.network.OpenDialoguePayload;
import com.rnmd.shadownpc.network.OpenNpcEditorPayload;
import net.fabricmc.api.ClientModInitializer;
import net.fabricmc.fabric.api.client.networking.v1.ClientPlayNetworking;

public final class ShadowNpcClient implements ClientModInitializer {
    @Override
    public void onInitializeClient() {
        ClientPlayNetworking.registerGlobalReceiver(OpenNpcEditorPayload.TYPE, (payload, context) ->
                context.client().setScreen(new NpcEditorScreen(payload))
        );

        ClientPlayNetworking.registerGlobalReceiver(OpenDialoguePayload.TYPE, (payload, context) ->
                context.client().setScreen(new DialogueScreen(payload))
        );

        System.out.println("SHADOW_NPC_CLIENT_OK");
    }
}
