package com.berlord.bertie_progression;

import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.SoundType;
import net.minecraft.world.level.block.state.BlockBehaviour;
import net.minecraft.world.level.material.MapColor;
import net.neoforged.neoforge.registries.DeferredBlock;
import net.neoforged.neoforge.registries.DeferredRegister;

public final class ModBlocks {
    public static final DeferredRegister.Blocks BLOCKS = DeferredRegister.createBlocks(BertieProgression.MODID);

    public static final DeferredBlock<Block> ECHO_LOCK = BLOCKS.register(
            "echo_lock",
            () -> new Block(BlockBehaviour.Properties.of()
                    .mapColor(MapColor.COLOR_CYAN).strength(3.0f).sound(SoundType.SCULK_SHRIEKER)));

    private ModBlocks() {}
}
