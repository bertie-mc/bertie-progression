package com.berlord.bertie_s1.item;

import com.berlord.bertie_s1.ModAttachments;
import net.minecraft.core.BlockPos;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.Blocks;

/**
 * A meal that sets you on fire and rewards you for surviving it.
 *
 * <p>Eating it drops a lava source on the eater's feet. Four ticks later - if they are still alive -
 * they get Fire Resistance for a minute. The delay is the point: you take the lava first and the
 * protection arrives after, so it is a gamble at low health rather than a free buff.
 *
 * <p>The countdown lives in a serialized attachment rather than a scheduled task so that quitting
 * mid-swallow cannot silently eat the reward, and so a player who dies in those four ticks simply
 * never reaches the grant.
 */
public class NetherlyMealItem extends Item {

    /**
     * Game ticks the eater must survive before the reward lands: long enough for FOUR lava hits but
     * not a fifth.
     *
     * <p>Derived from the jar, not from feel. {@code Entity.baseTick} calls {@code lavaHurt()} every
     * tick you are in lava, but {@code LivingEntity.hurt} rejects equal damage while
     * {@code invulnerableTime > 10}, and a landed hit sets it to 20 (NeoForge's
     * {@code DamageContainer.invulnerabilityTicksAfterAttack} default) decrementing once per tick.
     * So lava connects every <b>10</b> ticks: hits at t=0, 10, 20, 30, and the fifth at t=40.
     * 35 sits between the fourth and fifth.
     */
    public static final int SURVIVE_TICKS = 35;
    /** Fire Resistance duration on success: one minute. */
    public static final int REWARD_TICKS = 20 * 60;

    public NetherlyMealItem(Properties properties) {
        super(properties);
    }

    @Override
    public ItemStack finishUsingItem(ItemStack stack, Level level, LivingEntity entity) {
        ItemStack result = super.finishUsingItem(stack, level, entity);
        if (!level.isClientSide && entity instanceof Player player) {
            // Lava at the FEET, not the eye - it should burn the eater, not just decorate the floor.
            BlockPos at = player.blockPosition();
            if (level.getBlockState(at).canBeReplaced()) {
                level.setBlockAndUpdate(at, Blocks.LAVA.defaultBlockState());
            }
            player.setData(ModAttachments.MEAL_COUNTDOWN, SURVIVE_TICKS);
            // The Nether opens on the FIRST BITE, not on surviving it - berlord's rule is
            // "eaten once", and tying it to survival would strand a player who died to their
            // own meal with no way back to the recipe's dragon heart.
            player.setData(ModAttachments.NETHER_UNLOCKED, Boolean.TRUE);
        }
        return result;
    }

    /**
     * Called once per server tick for a player mid-countdown. Returns true when the countdown is
     * finished, so the caller can stop tracking.
     */
    public static void tickCountdown(Player player) {
        Integer left = player.getData(ModAttachments.MEAL_COUNTDOWN);
        if (left == null || left <= 0) {
            return;
        }
        if (left > 1) {
            player.setData(ModAttachments.MEAL_COUNTDOWN, left - 1);
            return;
        }
        player.setData(ModAttachments.MEAL_COUNTDOWN, 0);
        if (player.isAlive()) {
            player.addEffect(new MobEffectInstance(MobEffects.FIRE_RESISTANCE, REWARD_TICKS));
        }
    }
}
