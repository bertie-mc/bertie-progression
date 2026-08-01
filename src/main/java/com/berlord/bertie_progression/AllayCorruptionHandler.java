package com.berlord.bertie_progression;

import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.world.damagesource.DamageTypes;
import net.minecraft.world.entity.EquipmentSlot;
import com.berlord.bertie_progression.item.NetherlyMealItem;
import net.minecraft.world.entity.animal.allay.Allay;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.entity.item.ItemEntity;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.neoforge.event.tick.EntityTickEvent;

/**
 * Give an Allay an Arcane Crystal and it dies, leaving a Corrupted Arcane Crystal.
 *
 * <p>{@code forbidden_arcanus:corrupted_arcane_crystal} otherwise has no source in the pack. Its
 * references are its own block round-trip and two block loot tables, so nothing in the game ever
 * creates the first one.
 *
 * <p>Deliberately NOT an interaction hook. Watching for an allay that is simply HOLDING the crystal
 * means vanilla keeps ownership of the hand-off rules for free: you cannot give an allay an item
 * while its hands are full, and giving in creative does not consume the stack. Reusing those rules
 * avoids duplicating interaction behavior here.
 *
 * <p>Death is delayed a random 20-50 ticks, then dealt as real damage - "true death", so anything in
 * the pack that reacts to mob deaths sees it. It is generic damage with no attacker, so it credits
 * nobody, the way a TNT kill does not.
 *
 * <p>The held crystal is cleared in the same tick the allay dies. A vanilla allay drops what it is
 * holding, so without that the player would get the Arcane Crystal back as well as the corrupted one.
 */
public final class AllayCorruptionHandler {

    private static final ResourceLocation INPUT =
            ResourceLocation.parse("forbidden_arcanus:arcane_crystal");
    private static final ResourceLocation OUTPUT =
            ResourceLocation.parse("forbidden_arcanus:corrupted_arcane_crystal");

    private static final int DELAY_MIN = 20;
    private static final int DELAY_MAX = 50;

    @SubscribeEvent
    public static void onEntityTick(EntityTickEvent.Post event) {
        if (event.getEntity().level().isClientSide) {
            return;
        }
        // Netherly Meal shares this tick hook rather than adding a second one.
        if (event.getEntity() instanceof Player player) {
            NetherlyMealItem.tickCountdown(player);
            return;
        }
        if (!(event.getEntity() instanceof Allay allay)) {
            return;
        }
        Integer doom = allay.getData(ModAttachments.ALLAY_DOOM);
        if (doom == null || doom <= 0) {
            // not doomed yet: arm the countdown the moment it is holding an Arcane Crystal
            ItemStack held = allay.getItemBySlot(EquipmentSlot.MAINHAND);
            if (!held.isEmpty() && BuiltInRegistries.ITEM.getKey(held.getItem()).equals(INPUT)) {
                allay.setData(ModAttachments.ALLAY_DOOM,
                        DELAY_MIN + allay.getRandom().nextInt(DELAY_MAX - DELAY_MIN + 1));
            }
            return;
        }
        if (doom > 1) {
            allay.setData(ModAttachments.ALLAY_DOOM, doom - 1);
            return;
        }
        // Clear the hand FIRST - an allay drops what it holds, and the input must not come back.
        allay.setItemSlot(EquipmentSlot.MAINHAND, ItemStack.EMPTY);
        allay.setData(ModAttachments.ALLAY_DOOM, 0);

        Item out = BuiltInRegistries.ITEM.get(OUTPUT);
        if (out != null) {
            allay.level().addFreshEntity(new ItemEntity(allay.level(),
                    allay.getX(), allay.getY() + 0.25, allay.getZ(), new ItemStack(out)));
        }
        allay.hurt(allay.damageSources().source(DamageTypes.GENERIC), Float.MAX_VALUE);
    }

    private AllayCorruptionHandler() {}
}
