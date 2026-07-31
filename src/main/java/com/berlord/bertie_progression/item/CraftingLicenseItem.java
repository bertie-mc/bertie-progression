package com.berlord.bertie_progression.item;

import com.berlord.bertie_progression.ModAttachments;
import net.minecraft.network.chat.Component;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResultHolder;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.Level;

/**
 * One-shot consumable that permanently unlocks the vanilla 3x3 crafting grid for the using player
 * (see {@link com.berlord.bertie_progression.gate.CraftingGateHandler}). Replaces the Licensed Crafting
 * Plinth: the grid becomes an earned milestone instead of a place you must stand on.
 */
public class CraftingLicenseItem extends Item {

    public CraftingLicenseItem(Properties properties) {
        super(properties);
    }

    @Override
    public InteractionResultHolder<ItemStack> use(Level level, Player player, InteractionHand hand) {
        ItemStack stack = player.getItemInHand(hand);
        if (level.isClientSide) {
            return InteractionResultHolder.sidedSuccess(stack, true);
        }
        if (Boolean.TRUE.equals(player.getData(ModAttachments.CRAFTING_LICENSED.get()))) {
            player.displayClientMessage(
                    Component.translatable("message.bertie_progression.already_licensed"), true);
            return InteractionResultHolder.fail(stack);
        }
        player.setData(ModAttachments.CRAFTING_LICENSED.get(), Boolean.TRUE);
        if (!player.getAbilities().instabuild) {
            stack.shrink(1);
        }
        level.playSound(null, player.blockPosition(), SoundEvents.PLAYER_LEVELUP,
                SoundSource.PLAYERS, 0.7F, 1.2F);
        player.displayClientMessage(
                Component.translatable("message.bertie_progression.crafting_licensed"), false);
        return InteractionResultHolder.success(stack);
    }
}
