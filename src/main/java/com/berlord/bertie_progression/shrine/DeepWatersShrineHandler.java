package com.berlord.bertie_progression.shrine;

import net.minecraft.core.BlockPos;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.ResourceKey;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.state.BlockState;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.neoforge.event.entity.player.PlayerInteractEvent;

import java.util.HashSet;
import java.util.Set;

/**
 * Deep Waters Shrine (berlord 2026-07-27). Build the 7x7 shrine around a Conduit in the Deep
 * Waters dimension, then use a Crowned Jelly on the Conduit: the shrine collapses into a
 * Stormcall Altar pyramid and everything else inside the box floods.
 *
 * <p>Six block-layers tall. The "7x7x7" the design talks about counts the top crystal layer as two
 * high because those crystal models render a block above their own position — jar-verified, the
 * crystals are single blocks with no {@code half} property, so only six layers are matched.
 *
 * <p>Matching is ROTATION-TOLERANT: all four 90 degree orientations are tried. Block STATES are
 * ignored, only block identity is compared — the bundle crystal carries a {@code facing} property
 * that necessarily differs between rotations.
 */
public final class DeepWatersShrineHandler {

    /** The shrine only works in Deep Waters. */
    private static final ResourceLocation DIMENSION = ResourceLocation.parse("deepwaters:endlesscaves");
    private static final ResourceLocation TRIGGER = ResourceLocation.parse("deepwaters:crownedjelly");

    private static final ResourceLocation MOSSY = ResourceLocation.parse("minecraft:mossy_stone_bricks");
    private static final ResourceLocation PILLAR = ResourceLocation.parse("deepwaters:fopal_pillar");
    private static final ResourceLocation CONDUIT = ResourceLocation.parse("minecraft:conduit");
    private static final ResourceLocation LARGE = ResourceLocation.parse("deepwaters:cryslaaquamarine");
    private static final ResourceLocation BUNDLE = ResourceLocation.parse("deepwaters:crysmeaquamarine");
    private static final ResourceLocation SMALL = ResourceLocation.parse("deepwaters:cryssmaquamarine");

    private static final ResourceLocation ALTAR = ResourceLocation.parse("deepwaters:stormcall_altar");
    private static final ResourceLocation SEASTONE =
            ResourceLocation.parse("cataclysm:polished_azure_seastone");

    /** Layers bottom to top. Rows north->south, chars west->east. */
    private static final String[][] LAYERS = {
            {   // L1 floor
                "MMMMMMM",
                "MMMMMMM",
                "MMMMMMM",
                "MMMMMMM",
                "MMMMMMM",
                "MMMMMMM",
                "MMMMMMM"},
            {   // L2 pillar in a solid 3x3, four diagonal posts, crystals on the outer edge
                "..SBS..",
                ".M...M.",
                "S.MMM.S",
                "B.MPM.B",
                "S.MMM.S",
                ".M...M.",
                "..SBS.."},
            {   // L3 conduit at centre, diagonal lattice
                ".......",
                ".M...M.",
                "..M.M..",
                "...C...",
                "..M.M..",
                ".M...M.",
                "......."},
            {   // L4 = L2 without the external crystals
                ".......",
                ".M...M.",
                "..MMM..",
                "..MPM..",
                "..MMM..",
                ".M...M.",
                "......."},
            {   // L5 roof
                "MMMMMMM",
                "MMMMMMM",
                "MMMMMMM",
                "MMMMMMM",
                "MMMMMMM",
                "MMMMMMM",
                "MMMMMMM"},
            {   // L6 top crystals - ASYMMETRIC, and the centre is deliberately EMPTY
                "..SLS..",
                ".....B.",
                "S.S.S.S",
                "L...S.L",
                "SS...SS",
                ".......",
                "..SLS.."},
    };

    private static final int SIZE = 7;
    private static final int CONDUIT_LAYER = 2;   // L3, zero-indexed
    private static final int CENTRE = 3;          // d4, zero-indexed

    // Cuboid centred on the conduit that may contain ONLY shrine blocks and water (berlord).
    private static final int WATER_DOWN = 1;
    private static final int WATER_HORIZONTAL = 6;
    private static final int WATER_UP = 5;
    private static final int CLEAR_UP = 10;       // water OR air

    @SubscribeEvent
    public static void onRightClickBlock(PlayerInteractEvent.RightClickBlock event) {
        if (event.getHand() != InteractionHand.MAIN_HAND) return;

        ItemStack held = event.getItemStack();
        if (!BuiltInRegistries.ITEM.getKey(held.getItem()).equals(TRIGGER)) return;

        Level level = event.getLevel();
        BlockPos conduitPos = event.getPos();
        if (!isBlock(level, conduitPos, CONDUIT)) return;
        if (!level.dimension().location().equals(DIMENSION)) return;

        // Absent-mod guard: without Deep Waters / Cataclysm there is nothing to turn it into.
        Block altar = BuiltInRegistries.BLOCK.get(ALTAR);
        Block seastone = BuiltInRegistries.BLOCK.get(SEASTONE);
        if (altar == Blocks.AIR || seastone == Blocks.AIR) return;

        int rotation = findRotation(level, conduitPos);
        if (rotation < 0) return;   // not our structure - leave the interaction alone

        event.setCanceled(true);
        if (level.isClientSide) return;

        Set<BlockPos> shrine = shrineBlocks(conduitPos, rotation);
        if (!hasSpace(level, conduitPos, shrine)) {
            event.getEntity().displayClientMessage(
                    Component.translatable("message.bertie_progression.shrine_no_space"), true);
            return;   // jelly untouched on failure
        }

        transform(level, conduitPos, shrine, altar, seastone);

        Player player = event.getEntity();
        if (!player.getAbilities().instabuild) held.shrink(1);
        level.playSound(null, conduitPos, SoundEvents.CONDUIT_ACTIVATE, SoundSource.BLOCKS, 1.0f, 0.8f);
        player.displayClientMessage(Component.translatable("message.bertie_progression.shrine_formed"), true);
    }

    // ------------------------------------------------------------------ matching

    /** @return the rotation (0..3 quarter turns) the shrine is built at, or -1 if it is not there. */
    private static int findRotation(Level level, BlockPos conduitPos) {
        for (int rot = 0; rot < 4; rot++) {
            if (matches(level, conduitPos, rot)) return rot;
        }
        return -1;
    }

    private static boolean matches(Level level, BlockPos conduitPos, int rot) {
        for (int layer = 0; layer < LAYERS.length; layer++) {
            for (int row = 0; row < SIZE; row++) {
                for (int col = 0; col < SIZE; col++) {
                    ResourceLocation expected = idFor(LAYERS[layer][row].charAt(col));
                    BlockPos pos = cellPos(conduitPos, layer, row, col, rot);
                    if (expected == null) continue;   // '.' - contents irrelevant to the match
                    if (!isBlock(level, pos, expected)) return false;
                }
            }
        }
        return true;
    }

    /**
     * World position of a schematic cell. The conduit anchors the box: it sits at layer
     * CONDUIT_LAYER, cell (CENTRE, CENTRE), so every other cell is an offset from it.
     */
    private static BlockPos cellPos(BlockPos conduitPos, int layer, int row, int col, int rot) {
        int dx = col - CENTRE;
        int dz = row - CENTRE;
        int rx, rz;
        switch (rot) {
            case 1  -> { rx = -dz; rz = dx; }
            case 2  -> { rx = -dx; rz = -dz; }
            case 3  -> { rx = dz;  rz = -dx; }
            default -> { rx = dx;  rz = dz; }
        }
        return conduitPos.offset(rx, layer - CONDUIT_LAYER, rz);
    }

    private static ResourceLocation idFor(char c) {
        return switch (c) {
            case 'M' -> MOSSY;
            case 'P' -> PILLAR;
            case 'C' -> CONDUIT;
            case 'L' -> LARGE;
            case 'B' -> BUNDLE;
            case 'S' -> SMALL;
            default  -> null;
        };
    }

    /** Every world position the matched shrine actually occupies (non-empty schematic cells). */
    private static Set<BlockPos> shrineBlocks(BlockPos conduitPos, int rot) {
        Set<BlockPos> out = new HashSet<>();
        for (int layer = 0; layer < LAYERS.length; layer++) {
            for (int row = 0; row < SIZE; row++) {
                for (int col = 0; col < SIZE; col++) {
                    if (idFor(LAYERS[layer][row].charAt(col)) == null) continue;
                    out.add(cellPos(conduitPos, layer, row, col, rot));
                }
            }
        }
        return out;
    }

    // ------------------------------------------------------------------ space checks

    /**
     * Water/clearance around the conduit. berlord 2026-07-27: these numbers describe a <b>CUBOID
     * centred on the conduit that may contain nothing but shrine blocks and water</b> — not runs
     * or rays outward along each axis.
     *
     * <ul>
     *   <li><b>Water box:</b> x/z within {@link #WATER_HORIZONTAL}, y from -{@link #WATER_DOWN} to
     *       +{@link #WATER_UP}. Every block is either part of the shrine or WATER.</li>
     *   <li><b>Clearance box:</b> the same footprint, y from +{@code WATER_UP}+1 to
     *       +{@link #CLEAR_UP}. Every block is shrine, water or AIR.</li>
     * </ul>
     *
     * Note the shrine's floor sits at conduit-2, i.e. BELOW the water box, so the seabed the shrine
     * stands on is deliberately never inspected.
     */
    private static boolean hasSpace(Level level, BlockPos conduit, Set<BlockPos> shrine) {
        BlockPos.MutableBlockPos pos = new BlockPos.MutableBlockPos();
        for (int dx = -WATER_HORIZONTAL; dx <= WATER_HORIZONTAL; dx++) {
            for (int dz = -WATER_HORIZONTAL; dz <= WATER_HORIZONTAL; dz++) {
                for (int dy = -WATER_DOWN; dy <= CLEAR_UP; dy++) {
                    pos.set(conduit.getX() + dx, conduit.getY() + dy, conduit.getZ() + dz);
                    if (shrine.contains(pos)) continue;
                    BlockState state = level.getBlockState(pos);
                    if (!state.getFluidState().isEmpty()) continue;          // water: always fine
                    if (dy > WATER_UP && state.isAir()) continue;            // air: only up high
                    return false;
                }
            }
        }
        return true;
    }

    // ------------------------------------------------------------------ transform

    /**
     * Beacon-style pyramid with the altar where the conduit was: 5x5 two layers down, 3x3 one
     * layer down, altar at the conduit. Everything else the shrine occupied becomes water.
     */
    private static void transform(Level level, BlockPos conduit, Set<BlockPos> shrine,
                                  Block altar, Block seastone) {
        for (BlockPos pos : shrine) {
            level.setBlock(pos, Blocks.WATER.defaultBlockState(), Block.UPDATE_CLIENTS);
        }
        for (int dx = -2; dx <= 2; dx++) {
            for (int dz = -2; dz <= 2; dz++) {
                level.setBlock(conduit.offset(dx, -2, dz), seastone.defaultBlockState(),
                        Block.UPDATE_CLIENTS);
                if (Math.abs(dx) <= 1 && Math.abs(dz) <= 1) {
                    level.setBlock(conduit.offset(dx, -1, dz), seastone.defaultBlockState(),
                            Block.UPDATE_CLIENTS);
                }
            }
        }
        level.setBlockAndUpdate(conduit, altar.defaultBlockState());
    }

    private static boolean isBlock(Level level, BlockPos pos, ResourceLocation id) {
        BlockState state = level.getBlockState(pos);
        return BuiltInRegistries.BLOCK.getKey(state.getBlock()).equals(id);
    }

    private DeepWatersShrineHandler() {}
}
