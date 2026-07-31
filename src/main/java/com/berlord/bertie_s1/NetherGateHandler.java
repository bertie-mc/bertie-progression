package com.berlord.bertie_s1;

import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.level.Level;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.neoforge.event.entity.EntityTravelToDimensionEvent;

/**
 * The Nether is closed until you have eaten a Netherly Meal.
 *
 * <p>berlord's rule: a player can light the portal and stand in it, but nothing happens until the
 * meal has been eaten once. The unlock is permanent and survives death - it is a milestone, not a
 * buff, so the flag is a {@code copyOnDeath} attachment, the same shape the Crafting License uses.
 *
 * <p>Cancelling {@link EntityTravelToDimensionEvent} is what stops it. Note this gates travel to the
 * Nether by ANY route, not only a portal - the event carries the destination but not the cause, so a
 * teleport or a command would be refused too. That is the correct reading of "cannot enter the
 * Nether"; if berlord ever wants portals only, this needs a different hook.
 *
 * <p>Only players are gated. Mobs, items and everything else travel normally, so a portal still
 * works as a portal for the rest of the world.
 */
public final class NetherGateHandler {

    @SubscribeEvent
    public static void onTravel(EntityTravelToDimensionEvent event) {
        if (!(event.getEntity() instanceof ServerPlayer player)) {
            return;
        }
        if (!event.getDimension().equals(Level.NETHER)) {
            return;
        }
        if (Boolean.TRUE.equals(player.getData(ModAttachments.NETHER_UNLOCKED))) {
            return;
        }
        event.setCanceled(true);
        // Silence here would read as a broken portal, so say why - on the action bar, because the
        // event can fire repeatedly while the player stands in the frame.
        player.displayClientMessage(Component.translatable("message.bertie_s1.nether_locked"), true);
    }

    private NetherGateHandler() {}
}
