package com.berlord.bertie_s1;

import com.berlord.bertie_s1.gate.CraftingGateHandler;
import com.berlord.bertie_s1.forge.ForgeBedHandler;
import com.berlord.bertie_s1.forge.PedestalFormationHandler;
import com.berlord.bertie_s1.recipe.ModRecipes;
import com.berlord.bertie_s1.shrine.DeepWatersShrineHandler;
import net.neoforged.bus.api.IEventBus;
import net.neoforged.fml.common.Mod;
import net.neoforged.neoforge.common.NeoForge;

@Mod(BertieS1.MODID)
public final class BertieS1 {
    public static final String MODID = "bertie_s1";

    public BertieS1(IEventBus modBus) {
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
    }
}
