package com.berlord.bertie_s1.forge;

import com.berlord.bertie_s1.ModItems;
import net.minecraft.core.BlockPos;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.tags.FluidTags;
import net.minecraft.tags.TagKey;
import net.minecraft.core.registries.Registries;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.CampfireBlock;
import net.minecraft.world.level.block.state.BlockState;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.neoforge.event.entity.player.PlayerInteractEvent;

/**
 * Opening Mallet world interactions (demo tier of the OpeningFoundryHandler contract):
 *  - R04A  mallet strike on Dirt touching water -> Mud
 *  - R02A  cane press against water while carrying two Wood Slates -> Paper
 *  - R05   mallet strike on the exact two-layer Mud-Brick/campfire/log build -> slag:brick_forge
 *  - Bed recipes (BedRecipes.RECIPES): strike the placed Brick Forge holding the primary
 *    input in one hand and the Mallet in the other; sneak selects the alternate shaping.
 */
public final class ForgeBedHandler {

    private static final TagKey<Block> STRIPPED_LOGS_BLOCK =
            TagKey.create(Registries.BLOCK, ResourceLocation.parse("bertie_s1:stripped_logs"));

    @SubscribeEvent
    public static void onRightClickBlock(PlayerInteractEvent.RightClickBlock event) {
        if (event.getHand() != InteractionHand.MAIN_HAND) return;
        Player player = event.getEntity();
        Level level = event.getLevel();
        BlockPos pos = event.getPos();

        ItemStack main = player.getMainHandItem();
        ItemStack off = player.getOffhandItem();
        boolean malletMain = main.is(ModItems.OPENING_MALLET.get());
        boolean malletOff = off.is(ModItems.OPENING_MALLET.get());
        if (!malletMain && !malletOff) return;

        ItemStack primary = malletMain ? off : main;
        InteractionHand malletHand = malletMain ? InteractionHand.MAIN_HAND : InteractionHand.OFF_HAND;
        BlockState state = level.getBlockState(pos);

        // --- R04A: dirt touching natural water -> mud ---
        if (state.is(Blocks.DIRT) && primary.isEmpty()) {
            if (!touchesWater(level, pos)) return;
            event.setCanceled(true);
            if (level.isClientSide) return;
            level.setBlockAndUpdate(pos, Blocks.MUD.defaultBlockState());
            finishStrike(player, level, pos, malletHand);
            return;
        }

        // --- R02A: paper press — strike water-adjacent block with 3 Sugar Cane, 2 Wood Slates carried ---
        if (primary.is(net.minecraft.world.item.Items.SUGAR_CANE)
                && (touchesWater(level, pos) || level.getFluidState(pos).is(FluidTags.WATER))) {
            if (primary.getCount() < 3) { hint(player, level, "message.bertie_s1.paper_need_cane"); return; }
            if (countItem(player, "berlords_carving:wood_slate") < 2) {
                hint(player, level, "message.bertie_s1.paper_need_slates"); return;
            }
            event.setCanceled(true);
            if (level.isClientSide) return;
            primary.shrink(3);
            give(player, new ItemStack(net.minecraft.world.item.Items.PAPER, 3));
            finishStrike(player, level, pos, malletHand);
            return;
        }

        // --- R05: Brick Forge formation ---
        if (state.is(Blocks.MUD_BRICKS) && primary.isEmpty()) {
            if (tryFormBrickForge(event, player, level, pos, malletHand)) return;
        }

        // --- Bed recipes on the placed Brick Forge ---
        if (isBrickForge(state)) {
            handleBed(event, player, level, pos, primary, malletHand);
        }
    }

    private static boolean isBrickForge(BlockState state) {
        return BuiltInRegistries.BLOCK.getKey(state.getBlock())
                .equals(ResourceLocation.parse("slag:brick_forge"));
    }

    private static boolean touchesWater(Level level, BlockPos pos) {
        for (var dir : net.minecraft.core.Direction.values()) {
            if (level.getFluidState(pos.relative(dir)).is(FluidTags.WATER)) return true;
        }
        return false;
    }

    private static void handleBed(PlayerInteractEvent.RightClickBlock event, Player player,
                                  Level level, BlockPos pos, ItemStack primary, InteractionHand malletHand) {
        boolean sneak = player.isShiftKeyDown();
        for (BedRecipes.BedRecipe r : BedRecipes.RECIPES) {
            if (r.sneak() != sneak) continue;
            if (!r.primary().what().test(primary) || primary.getCount() < r.primary().count()) continue;
            if (r.secondary() != null && countMatching(player, r.secondary().what()) < r.secondary().count()) continue;
            if (r.tertiary() != null && countMatching(player, r.tertiary().what()) < r.tertiary().count()) continue;

            Item result = BuiltInRegistries.ITEM.get(ResourceLocation.parse(r.resultId()));
            if (result == net.minecraft.world.item.Items.AIR) return; // target mod absent

            event.setCanceled(true);
            if (level.isClientSide) return;

            primary.shrink(r.primary().count());
            if (r.secondary() != null) consumeMatching(player, r.secondary().what(), r.secondary().count());
            if (r.tertiary() != null) consumeMatching(player, r.tertiary().what(), r.tertiary().count());
            give(player, new ItemStack(result, r.resultCount()));
            if (r.extraReturnId() != null) {
                Item ret = BuiltInRegistries.ITEM.get(ResourceLocation.parse(r.extraReturnId()));
                if (ret != net.minecraft.world.item.Items.AIR)
                    give(player, new ItemStack(ret, r.extraReturnCount()));
            }
            finishStrike(player, level, pos, malletHand);
            return;
        }
    }

    /**
     * R05 exact two-layer build: 3x3 ring of Mud Bricks around an UNLIT campfire,
     * four stripped logs directly above the corner bricks. Striking any ring brick
     * consumes the build and forms the Brick Forge at the center.
     */
    private static boolean tryFormBrickForge(PlayerInteractEvent.RightClickBlock event, Player player,
                                             Level level, BlockPos struck, InteractionHand malletHand) {
        Block forge = BuiltInRegistries.BLOCK.get(ResourceLocation.parse("slag:brick_forge"));
        if (BuiltInRegistries.BLOCK.getKey(forge).getPath().equals("air")) return false;

        for (int dx = -1; dx <= 1; dx++) {
            for (int dz = -1; dz <= 1; dz++) {
                if (dx == 0 && dz == 0) continue;
                BlockPos center = struck.offset(-dx, 0, -dz);
                if (!isUnlitCampfire(level.getBlockState(center))) continue;
                if (!ringIsMudBricks(level, center)) continue;
                if (!cornersHaveStrippedLogs(level, center)) continue;

                event.setCanceled(true);
                if (level.isClientSide) return true;

                for (int rx = -1; rx <= 1; rx++)
                    for (int rz = -1; rz <= 1; rz++) {
                        if (rx == 0 && rz == 0) continue;
                        level.removeBlock(center.offset(rx, 0, rz), false);
                        if (rx != 0 && rz != 0) level.removeBlock(center.offset(rx, 1, rz), false);
                    }
                level.setBlockAndUpdate(center, forge.defaultBlockState());
                level.playSound(null, center, SoundEvents.FIRECHARGE_USE, SoundSource.BLOCKS, 1f, 0.8f);
                finishStrike(player, level, center, malletHand);
                player.displayClientMessage(Component.translatable("message.bertie_s1.forge_formed"), true);
                return true;
            }
        }
        return false;
    }

    private static boolean isUnlitCampfire(BlockState state) {
        return state.is(Blocks.CAMPFIRE) && !state.getValue(CampfireBlock.LIT);
    }

    private static boolean ringIsMudBricks(Level level, BlockPos center) {
        for (int dx = -1; dx <= 1; dx++)
            for (int dz = -1; dz <= 1; dz++) {
                if (dx == 0 && dz == 0) continue;
                if (!level.getBlockState(center.offset(dx, 0, dz)).is(Blocks.MUD_BRICKS)) return false;
            }
        return true;
    }

    private static boolean cornersHaveStrippedLogs(Level level, BlockPos center) {
        int[][] corners = {{-1, -1}, {-1, 1}, {1, -1}, {1, 1}};
        for (int[] c : corners) {
            if (!level.getBlockState(center.offset(c[0], 1, c[1])).is(STRIPPED_LOGS_BLOCK)) return false;
        }
        return true;
    }

    private static int countItem(Player player, String id) {
        ResourceLocation rl = ResourceLocation.parse(id);
        int total = 0;
        for (ItemStack s : player.getInventory().items) {
            if (!s.isEmpty() && BuiltInRegistries.ITEM.getKey(s.getItem()).equals(rl)) total += s.getCount();
        }
        return total;
    }

    private static int countMatching(Player player, BedRecipes.StackPredicate pred) {
        int total = 0;
        for (ItemStack s : player.getInventory().items) if (pred.test(s)) total += s.getCount();
        return total;
    }

    private static void consumeMatching(Player player, BedRecipes.StackPredicate pred, int count) {
        int remaining = count;
        for (ItemStack s : player.getInventory().items) {
            if (remaining <= 0) break;
            if (pred.test(s)) {
                int take = Math.min(remaining, s.getCount());
                s.shrink(take);
                remaining -= take;
            }
        }
    }

    private static void give(Player player, ItemStack stack) {
        player.getInventory().placeItemBackInInventory(stack);
    }

    private static void finishStrike(Player player, Level level, BlockPos pos, InteractionHand malletHand) {
        level.playSound(null, pos, SoundEvents.STONE_HIT, SoundSource.BLOCKS, 0.8f, 1.1f);
        ItemStack mallet = player.getItemInHand(malletHand);
        if (mallet.is(ModItems.OPENING_MALLET.get())) {
            mallet.hurtAndBreak(1, player, malletHand == InteractionHand.MAIN_HAND
                    ? net.minecraft.world.entity.EquipmentSlot.MAINHAND
                    : net.minecraft.world.entity.EquipmentSlot.OFFHAND);
        }
    }

    private static void hint(Player player, Level level, String key) {
        if (!level.isClientSide) player.displayClientMessage(Component.translatable(key), true);
    }

    private ForgeBedHandler() {}
}
