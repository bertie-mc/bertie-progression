package com.berlord.bertie_progression;

import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.SoundType;
import net.minecraft.world.level.block.state.BlockBehaviour;
import net.minecraft.world.level.material.MapColor;
import net.neoforged.neoforge.registries.DeferredBlock;
import net.neoforged.neoforge.registries.DeferredRegister;

public final class ModBlocks {
    public static final DeferredRegister.Blocks BLOCKS = DeferredRegister.createBlocks(BertieProgression.MODID);

    // LICENSED_CRAFTING_PLINTH removed (berlord batch 4) — the 3x3 gate is now the consumable
    // Crafting License (see ModAttachments.CRAFTING_LICENSED / CraftingLicenseItem).

    // VICTORY_LEDGER removed (berlord 2026-07-25): the block, its SavedData kill tally and the
    // BossProofHandler that fed it are gone — nothing read the data after the proof items were cut.

    public static final DeferredBlock<Block> ECHO_LOCK = BLOCKS.register(
            "echo_lock",
            () -> new Block(BlockBehaviour.Properties.of()
                    .mapColor(MapColor.COLOR_CYAN).strength(3.0f).sound(SoundType.SCULK_SHRIEKER)));

    private ModBlocks() {}
}
