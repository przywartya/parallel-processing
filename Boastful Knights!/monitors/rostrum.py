from threading import Condition, Lock


class Rostrum:
    knights = []
    neighs_talking_cvs = []
    king_talking_cvs = []
    monitor_lock = Lock()

    def register_knights(self, knights):
        self.knights = knights
        self.neighs_talking_cvs = [Condition(self.monitor_lock) for _ in knights]
        self.king_talking_cvs = [Condition(self.monitor_lock) for _ in knights]

    def start_talking(self, knight):
        with self.monitor_lock:
            print("{}. Attempts talking.".format(knight))
            k_idx = knight.idx
            while not self.is_king(k_idx) and 'listening_to_king' in knight.status:
                # Wait until Knight finishes his talking.
                print("{}. King is talking. Waiting.".format(knight))
                knight.status.append('waiting_for_king')
                self.king_talking_cvs[k_idx].wait()
                knight.status.remove('waiting_for_king')
            l_neigh = self.knights[knight.l_idx]
            r_neigh = self.knights[knight.r_idx]
            while 'talking' in l_neigh.status or 'talking' in r_neigh.status:
                print("{}. Neighbour(s) are talking. Waiting.".format(knight))
                knight.status.append('waiting_for_neigh')
                self.neighs_talking_cvs[k_idx].wait()
                knight.status.remove('waiting_for_neigh')
                print("{}. Signalized.".format(knight))
            knight.status = ['talking']
            # When kings starts talking he sets status listening to king
            # for everyone who is not talking
            if self.is_king(k_idx):
                for i in range(1, len(self.knights)):
                    if 'not_talking' in self.knights[i].status:
                        self.knights[i].status.append('listening_to_king')

    def stop_talking(self, knight):
        with self.monitor_lock:
            print("{}. Stops talking.".format(knight))
            k_idx = knight.idx
            l_neigh = self.knights[knight.l_idx]
            ll_neigh = self.knights[l_neigh.l_idx]
            r_neigh = self.knights[knight.r_idx]
            rr_neigh = self.knights[r_neigh.r_idx]
            if self.is_king(k_idx):
                knight.status = ['not_talking']
                # If King has finished his talking
                # consider every Knight in listening to king status.
                for i in range(1, len(self.knights)):
                    # If Knight is waiting for someone to end talking
                    # check if it is necessary to wake him up - check his neighbours.
                    if 'waiting_for_neigh' in self.knights[i].status:
                        left = self.knights[self.knights[i].l_idx]
                        right = self.knights[self.knights[i].r_idx]
                        if 'not_talking' in left.status and 'not_talking' in right.status:
                            self.neighs_talking_cvs[i].notify()
                            i += 1
                    # If Knight is waiting for King to end talking
                    # then simply wake him up. We don't have to check his neighbours
                    # because after he wakes from waiting for the king he checks
                    # if he can talk (he checks his neighs). If not he goes to sleep.
                    # Hence no need for double check.
                    elif 'waiting_for_king' in self.knights[i].status:
                        self.king_talking_cvs[i].notify()
                    # For everyone else (who does not want to speak)
                    # Bring back his original state - not talking.
                    else:
                        self.knights[i].status = ['not_talking']
                    # knights[i] is no longer listening to king
                    # so remove the listening to king status.
                    if 'listening_to_king' in self.knights[i].status:
                        self.knights[i].status.remove('listening_to_king')
            else:
                # If Knight (not King) has finished his talking
                # and in the meantime King is still talking
                # then set Knight's status to listening to king.
                # not talking otherwise.
                if 'talking' in self.knights[0].status:
                    knight.status = ['listening_to_king']
                else:
                    knight.status = ['not_talking']
                # If Knight has finished his talking
                # and his first neighbours are waiting to tell something
                # and his second neighbors are not talking (or waiting)
                # then wake those first neighbours up.
                if 'waiting_for_neigh' in l_neigh.status and 'not_talking' in ll_neigh.status:
                    print("{}. Signal {}.".format(knight, l_neigh))
                    self.neighs_talking_cvs[l_neigh.idx].notify()
                if 'waiting_for_neigh' in r_neigh.status and 'not_talking' in rr_neigh.status and \
                        not 'talking' in self.knights[0].status:
                    print("{}. Signal {}.".format(knight, r_neigh))
                    self.neighs_talking_cvs[r_neigh.idx].notify()

    @staticmethod
    def is_king(idx):
        return idx == 0

