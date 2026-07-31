package com.berlord.bertie_progression;

import com.berlord.bertie_progression.gate.CraftingGateHandler;
import com.berlord.bertie_progression.forge.ForgeBedHandler;
import com.berlord.bertie_progression.forge.PedestalFormationHandler;
import com.berlord.bertie_progression.recipe.ModRecipes;
import com.berlord.bertie_progression.shrine.DeepWatersShrineHandler;
import net.neoforged.bus.api.IEventBus;
import net.neoforged.fml.common.Mod;
import net.neoforged.neoforge.common.NeoForge;

@Mod(BertieProgression.MODID)
public final class BertieProgression {
    public static final String MODID = "bertie_progression";

    public BertieProgression(IEventBus modBus) {
        ModItems.ITEMS.register(modBus);
        ModBlocks.BLOCKS.register(modBus);
        ModItems.DATA_COMPONENTS.register(modBus);
        ModItems.TABS.register(modBus);
        ModAttachments.ATTACHMENTS.register(modBus);
        ModRecipes.SERIALIZERS.register(modBus);
        // BuildCreativeModeTabContentsEvent is a MOD-bus event, not a game-bus one.
        modBus.register(RemovedItems.class);

        NeoForge.EVENT_BUS.register(CraftingGateHandler.class);
        NeoForge.EVENT_BUS.register(ForgeBedHandler.class);
        NeoForge.EVENT_BUS.register(PedestalFormationHandler.class);
        NeoForge.EVENT_BUS.register(DeepWatersShrineHandler.class);
        NeoForge.EVENT_BUS.register(AllayCorruptionHandler.class);
        NeoForge.EVENT_BUS.register(NetherGateHandler.class);
    }
}
