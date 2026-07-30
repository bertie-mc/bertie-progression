package com.berlord.bertie_s1.item;

import com.mojang.datafixers.util.Pair;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Holder;
import net.minecraft.core.HolderSet;
import net.minecraft.core.registries.Registries;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.ResourceKey;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResultHolder;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.entity.projectile.EyeOfEnder;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.levelgen.structure.Structure;

import java.util.Optional;

/**
 * Eye-of-Ender-style locator: on use it finds the nearest instance of a target structure and
 * launches a signalling {@link EyeOfEnder} toward it (the vanilla eye behaviour — flies up, drifts
 * toward the target, then drops or shatters). Unlike {@link LocatorItem} (which just prints coords),
 * this gives the player the familiar throw-and-follow flight. Used for the Weeping Well
 * ({@code malum:weeping_well}).
 */
public class WeepingEyeItem extends Item {

    private final ResourceLocation structureId;
    /** Chunks. See LocatorItem - same rule, same default. */
    private final int searchRadius;

    public WeepingEyeItem(Properties properties, ResourceLocation structureId, int searchRadius) {
        super(properties);
        this.structureId = structureId;
        this.searchRadius = searchRadius;
    }

    @Override
    public InteractionResultHolder<ItemStack> use(Level level, Player player, InteractionHand hand) {
        ItemStack stack = player.getItemInHand(hand);
        if (!(player instanceof ServerPlayer serverPlayer) || !(level instanceof ServerLevel serverLevel)) {
            return InteractionResultHolder.sidedSuccess(stack, true);
        }
        ResourceKey<Structure> key = ResourceKey.create(Registries.STRUCTURE, structureId);
        Optional<Holder.Reference<Structure>> holder =
                serverLevel.registryAccess().registryOrThrow(Registries.STRUCTURE).getHolder(key);
        if (holder.isEmpty()) {
            serverPlayer.displayClientMessage(
                    Component.translatable("message.bertie_s1.locator_missing", structureId.toString()), true);
            return InteractionResultHolder.fail(stack);
        }
        Pair<BlockPos, Holder<Structure>> found = serverLevel.getChunkSource().getGenerator()
                .findNearestMapStructure(serverLevel, HolderSet.direct(holder.get()),
                        serverPlayer.blockPosition(), searchRadius, false);
        if (found == null) {
            serverPlayer.displayClientMessage(Component.translatable("message.bertie_s1.locator_none"), true);
            return InteractionResultHolder.fail(stack);
        }
        BlockPos pos = found.getFirst();

        EyeOfEnder eye = new EyeOfEnder(level, player.getX(), player.getY(0.5), player.getZ());
        eye.setItem(stack);
        eye.signalTo(pos);
        level.addFreshEntity(eye);

        level.playSound(null, player.getX(), player.getY(), player.getZ(),
                SoundEvents.ENDER_EYE_LAUNCH, SoundSource.NEUTRAL, 0.5F, 0.4F / (level.getRandom().nextFloat() * 0.4F + 0.8F));
        player.awardStat(net.minecraft.stats.Stats.ITEM_USED.get(this));
        player.getCooldowns().addCooldown(this, 20);
        if (!player.getAbilities().instabuild) {
            stack.shrink(1);
        }
        player.swing(hand, true);
        return InteractionResultHolder.success(stack);
    }
}
