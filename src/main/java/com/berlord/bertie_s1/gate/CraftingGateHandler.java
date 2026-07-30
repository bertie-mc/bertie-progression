package com.berlord.bertie_s1.gate;

import com.berlord.bertie_s1.ModAttachments;
import net.minecraft.network.chat.Component;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.state.BlockState;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.neoforge.event.entity.player.PlayerInteractEvent;

/**
 * Stage-1 3x3 gate: a vanilla Crafting Table only opens for a player who has consumed a Crafting
 * License ({@link com.berlord.bertie_s1.item.CraftingLicenseItem}). Structure/loot tables stay
 * placeable and visible but refuse to open. Replaces the Licensed Crafting Plinth check — the
 * unlock is now a permanent per-player milestone rather than a place you must stand on.
 */
public final class CraftingGateHandler {

    @SubscribeEvent
    public static void onRightClickBlock(PlayerInteractEvent.RightClickBlock event) {
        Level level = event.getLevel();
        BlockState state = level.getBlockState(event.getPos());
        if (!state.is(Blocks.CRAFTING_TABLE)) return;

        Player player = event.getEntity();
        if (player.isSpectator()) return;
        // Sneak-use with an item = ordinary block placement etc.; the GUI only opens on
        // non-sneak use, which is the path we gate.
        if (player.isShiftKeyDown()) return;

        if (Boolean.TRUE.equals(player.getData(ModAttachments.CRAFTING_LICENSED.get()))) return;

        event.setCanceled(true);
        if (!level.isClientSide) {
            player.displayClientMessage(
                    Component.translatable("message.bertie_s1.table_unlicensed"), true);
        }
    }

    private CraftingGateHandler() {}
}
