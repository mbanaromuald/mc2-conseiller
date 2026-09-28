"""Données simulées (démo) : portefeuille MC2, marchés, prix hebdomadaires du sac de 100 kg (FCFA)."""
FARMERS = {
    "Aminatou B. · Ngaoundéré · Maïs": dict(crop="Maïs", lat=7.32, lon=13.58, zone="Ngaoundéré", credit=450_000),
    "Jean-Paul K. · Bafoussam · Tomates": dict(crop="Tomate", lat=5.48, lon=10.42, zone="Bafoussam", credit=600_000),
    "Marie-Claire E. · Mbalmayo · Manioc": dict(crop="Manioc", lat=3.52, lon=11.50, zone="Mbalmayo", credit=350_000),
}
WEEKS = ["S-6", "S-5", "S-4", "S-3", "S-2", "S-1", "Auj."]
PRICES = {
    "Maïs": {"Ngaoundéré": [21000, 21500, 22000, 22500, 23000, 23500, 24000],
             "Bafoussam": [24000, 24500, 25000, 26500, 27000, 26500, 27500],
             "Yaoundé": [27000, 27500, 28000, 28500, 30000, 31000, 31500],
             "Douala": [28000, 28500, 29500, 30000, 30500, 30000, 29500]},
    "Tomate": {"Bafoussam": [18000, 17000, 16000, 15500, 17000, 19000, 21000],
               "Yaoundé": [22000, 21000, 21500, 22500, 24000, 26000, 27500],
               "Douala": [23000, 22500, 23000, 24500, 25500, 27000, 26000]},
    "Manioc": {"Mbalmayo": [9000, 9000, 9500, 9500, 10000, 10000, 10500],
               "Yaoundé": [11000, 11500, 11500, 12000, 12500, 12500, 13000],
               "Douala": [12500, 12500, 13000, 13500, 13500, 14000, 14500]},
}
# coût de transport par sac depuis la zone du producteur (FCFA)
TRANSPORT = {
    "Ngaoundéré": {"Ngaoundéré": 0, "Bafoussam": 2500, "Yaoundé": 3500, "Douala": 4500},
    "Bafoussam": {"Bafoussam": 0, "Yaoundé": 1800, "Douala": 1500},
    "Mbalmayo": {"Mbalmayo": 0, "Yaoundé": 800, "Douala": 2500},
}
