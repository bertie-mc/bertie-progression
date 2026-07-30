package com.berlord.bertie_s1;

import net.neoforged.api.distmarker.Dist;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.ModList;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.fml.event.lifecycle.FMLClientSetupEvent;

/**
 * Client-only setup. Currently just registers the Deep Waters Shrine ponder scene.
 *
 * <p>Ponder ships JarJar-embedded inside Create, so it is an optional dependency: the plugin class
 * is referenced ONLY from inside a lambda that runs after the ModList check, so its ponder imports
 * are never classloaded when Create is absent.
 */
@EventBusSubscriber(modid = BertieS1.MODID, value = Dist.CLIENT)
public final class ClientSetup {

    @SubscribeEvent
    static void onClientSetup(FMLClientSetupEvent event) {
        if (!ModList.get().isLoaded("ponder")) return;
        event.enqueueWork(() -> com.berlord.bertie_s1.shrine.ShrinePonderPlugin.register());
    }

    private ClientSetup() {}
}
