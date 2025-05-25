import json
import os
import struct
from json import JSONEncoder
from pprint import pprint

from django.db.models import Q

TERMINATOR_NULL = 0

BLOCK_SIZE = 56
SLOT_OFFSET = 484
SLOT_DATA_SIZE = (8 + (4 * BLOCK_SIZE))
STAT_DATA_OFFSET = 112
STAT_DATA_SIZE = 22
FORCE_TYPE_ABILITIES = {
    "182": {
        "name": 'Pixilate',
        "forced_from": 'Normal',
        "forced_type": 'Fairy'
    },
    "96": {
        "name": 'Normalize',
        "forced_from": '*',
        "forced_type": 'Normal'
    },
    "184": {
        "name": 'Aerilate',
        "forced_from": 'Normal',
        "forced_type": 'Flying'
    },
    "206": {
        "name": 'Galvanize',
        "forced_from": 'Normal',
        "forced_type": 'Electric'
    },
    "174": {
        "name": 'Refrigerate',
        "forced_from": 'Normal',
        "forced_type": 'Ice'
    }
}


def clean_nick_data(nick_elements):
    result = ''
    for char in nick_elements:
        if char == 0:
            return result
        else:
            result += chr(char)
    return result


def clamp(value, min_value=1, max_value=251):
    if min_value and value < min_value:
        return min_value

    if max_value and value > max_value:
        return max_value

    return value


class PokemonBytes:
    def __new__(cls, encrypted_data, *args, **kwargs):
        obj = super().__new__(cls)
        return obj

    def __init__(self, encrypted_data, *args, **kwargs):
        super().__init__()
        self.warning = False
        if encrypted_data[0] != 0:
            self.warning = True

        len_needed = 0
        if len(encrypted_data) < 260:
            encrypted_data_len = len(encrypted_data)
            len_needed = 260 - encrypted_data_len
        decrypted_data = decrypt_data(encrypted_data) + bytes([1] * len_needed)
        self.raw_data = decrypted_data

    def get_suffix(self):
        form = self.form
        match self.dex_number:
            # bit 0: fateful encounter flag
            # bit 1: female-adds 2 to resulting form variable, so 2 or 10 instead of 0 or 8
            # bit 2: genderless-adds 4, so 4 or 12
            # bits 3-7: form change flags-8 typical starting point then increases by 8, so 8, 16, 24, etc
            case 641 | 642 | 645:
                if form > 0:  ### Therian forms of Tornadus, Thundurus, Landorus
                    return "therian"
                else:
                    return 'incarnate'
            case 6:  # Charizard
                match form:
                    case 8 | 10:
                        return 'mega-x'
                    case 16 | 18:
                        return 'mega-y'
            case 20:  # (Alolan) Raticate
                match form:
                    case 0 | 2:
                        return None
                    case _:  # accounts for totems
                        return 'alola'
            case 25:  # Pikachu partner forms
                match form:
                    case 0 | 2:
                        return None
                    case _:  # no idea how many partner forms there are, but they're all here apparently
                        return "partner"
            case 105:  # (Alolan) Marowak
                match form:
                    case 0 | 2:
                        return None
                    case _:
                        return 'alola'
            case 150:  ### Mewtwo
                match form:
                    case 4:
                        return None
                    case 12:
                        return 'mega-x'
                    case 20:  ### Mewtwo Y
                        return 'mega-y'
            case 151:  ### Mew, not honestly sure why this one is weird
                return None
            case 201:  ### Unown
                return None
            case 351:  ### Castform
                match form:
                    case 8 | 10:
                        return "sunny"
                    case 16 | 18:
                        return "rainy"
                    case 24 | 26:
                        return "snowy"
            case 382:  ### Kyogre
                match form:
                    case 12:
                        return "primal"
            case 383:  ### Groudon
                match form:
                    case 12:
                        return "primal"
            case 386:  ### Deoxys
                match form:
                    case 4:
                        return None
                    case 12:
                        return "attack"
                    case 20:
                        return "defense"
                    case 28:
                        return "speed"
            case 412:  ### Burmy
                return None
            case 413:  ### Wormadam
                match form:
                    case 10:
                        return "sandy"
                    case 18:
                        return "trash"
                    case 2:
                        return "plant"
            case 414:  ### Mothim
                return None
            case 421:  ### Cherrim
                return None
            case 422:  ### Shellos
                return None
            case 423:  ### Gastrodon
                return None
            case 479:  ### Rotom
                match form:
                    case 12:
                        return "heat"
                    case 20:
                        return "wash"
                    case 28:
                        return "frost"
                    case 36:
                        return "fan"
                    case 44:
                        return "mow"
            case 487:  ### Giratina
                match form:
                    case 12:
                        return "origin"
            case 492:  ### Shaymin
                match form:
                    case 12:
                        return "sky"
            case 550:  ### Basculin
                return None
            case 555:  ### Darmanitan
                match form:
                    case 0 | 2:
                        return None
                    case 8 | 10:
                        return "zen"
            case 585:  ### Deerling
                return None
            case 586:  ### Sawsbuck
                return None
            case 646:  ### Kyurem
                match form:
                    case 12:
                        return "white"
                match form:
                    case 20:
                        return "black"
            case 647:  ### Keldeo
                return None
            case 648:  ### Meloetta
                match form:
                    case 12:
                        return "pirouette"
                    case 4:  # base form lmao
                        return "aria"
            case 649:  ### Genesect
                return None
            case 658:  ### Greninja
                match form:
                    case 8 | 16:
                        return "ash"
            case 664 | 665 | 666 | 669:  ### Scatterbug, Spewda, Vivillon, Flabébé
                return None
            case 670:  ### Floette
                match form:
                    case 42:  # 0 8 16 24 32 40
                        return "eternal"
                    case _:
                        return None
            case 671:  ### Florges
                return None
            case 676:  ### Furfrou
                return None
            case 678:  ### Meowstic
                match form:
                    case 0 | 8:
                        return None
                    case 10:
                        return "f"
            case 681:  ### Aegislash
                match form:
                    case 0 | 2:
                        return "shield"
                    case 8 | 10:
                        return "blade"
            case 684:  ### Swirlix (not sure if this is useful but testing)
                return None
            case 710:  ### Pumpkaboo
                match form:
                    case 8 | 10:
                        return "average"
                    case 16 | 18:
                        return "large"
                    case 24 | 26:
                        return "super"
                    case _:
                        return None
            case 711:  ### Gourgeist
                match form:
                    case 8 | 10:
                        return "average"
                    case 16 | 18:
                        return "large"
                    case 24 | 26:
                        return "super"
                    case _:
                        return None
            case 716:  ### Xerneas
                return None
            case 718:  ### Zygarde only needed for gen 7
                match form:
                    case 4:
                        return None
                    case 12:
                        return "10"
                    case 20 | 36:
                        return "complete"
            case 720:  ### Hoopa
                match form:
                    case 4:
                        return None
                    case 12:
                        return "unbound"
            case 741:  ### Oricorio
                match form:
                    case 8 | 10:
                        return "pom-pom"
                    case 16 | 18:
                        return "pau"
                    case 24 | 26:
                        return "sensu"
                    case _:
                        return "baile"
            case 745:  ### Lycanroc
                match form:
                    case 16 | 18:
                        return "dusk"
                    case 8 | 10:
                        return "midnight"
            case 746:  ### Wishiwashi
                match form:
                    case 0 | 2:
                        return None
                    case _:  # accounts for totem form
                        return 'school'
            case 774:  ### Minior 4 12 20 28 36 44 52 60
                match form:
                    case 12 | 20 | 28 | 36 | 44 | 52 | 60:  # 60 is red
                        return "core"
            case 800:  ### Necrozma
                match form:
                    case 4:
                        return None
                    case 12:
                        return "dusk"
                    case 20:
                        return "dawn"
                    case 28:
                        return "ultra"
            case 801:  ### Magearna
                return None
            case 19 | 20 | 26 | 27 | 28 | 37 | 38 | 50 | 51 | 52 | 53 | 74 | 75 | 76 | 88 | 89 | 103:  ###alolan forms-none have separate forms so just case them for if their form > 0
                match form:
                    case 8 | 10 | 12:  # honestly not sure if any are genderless but sure
                        return 'alola'
                    case _:
                        return None
            case 735 | 738 | 743 | 752 | 754 | 758 | 777 | 778 | 784:  # totem mons that aren't already accounted for elsewhere (totem-sized mons are likely a different form)
                match form:
                    case _:
                        return None
            case _:
                if form > 0 and form != 2 and form != 4:
                    return 'mega'
                else:
                    return None

    def get_atts(self):
        self.dex_number = struct.unpack("<H", self.raw_data[0x8:0xA])[0]
        if self.dex_number == 0:
            return

        self.pid = struct.unpack("<H", self.raw_data[0x18:0x1A])[0]
        self.form = struct.unpack("B", self.raw_data[0x1D:0x1E])[0]
        self.held_item_num = str(struct.unpack("<H", self.raw_data[0xA:0xC])[0])
        self.ability_num = struct.unpack("B", self.raw_data[0x14:0x15])[0]  # Ability
        self.nature_num = struct.unpack("B", self.raw_data[0x1C:0x1D])[0]  ## Nature
        self.level = struct.unpack("B", self.raw_data[116:117])[0]  ### Current level
        self.ev_hp = struct.unpack("B", self.raw_data[0x1E:0x1F])[0]
        self.ev_attack = struct.unpack("B", self.raw_data[0x1F:0x20])[0]
        self.ev_defense = struct.unpack("B", self.raw_data[0x20:0x21])[0]
        self.ev_speed = struct.unpack("B", self.raw_data[0x21:0x22])[0]
        self.ev_spatk = struct.unpack("B", self.raw_data[0x22:0x23])[0]
        self.ev_spdef = struct.unpack("B", self.raw_data[0x23:0x24])[0]
        ivloc = struct.unpack("<I", self.raw_data[0x74:0x78])[0]
        self.iv_hp = (ivloc >> 0) & 0x1F  ############################## HP IV
        self.iv_attack = (ivloc >> 5) & 0x1F  ############################## Attack IV
        self.iv_defense = (ivloc >> 10) & 0x1F  ############################# Defense IV
        self.iv_speed = (ivloc >> 15) & 0x1F  ############################# Speed IV
        self.iv_spatk = (ivloc >> 20) & 0x1F  ############################# Special attack IV
        self.iv_spdef = (ivloc >> 25) & 0x1F  ############################# Special defense IV

        mote = struct.unpack("HHHHHHHHHHHHH", self.raw_data[64:90])
        self.mote = clean_nick_data(mote)
        self.suffix = self.get_suffix()
        print(self.mote)

        def moves(self):
            move1 = ((0x5A, 0x5C), (0x62, 0x63))
            move2 = ((0x5C, 0x5E), (0x63, 0x64))
            move3 = ((0x5E, 0x60), (0x64, 0x65))
            move4 = ((0x60, 0x62), (0x65, 0x66))
            for ml, pl in (move1, move2, move3, move4):
                move_num = struct.unpack("<H", self.raw_data[ml[0]:ml[1]])[0]
                with open('data/move_data.json') as move_file, open('data/special_move_data.json') as special_move_file:
                    move_json = json.load(move_file)
                    if str(move_num) not in move_json:
                        continue
                    move_data = move_json[str(move_num)]
                    special_move_data = json.load(special_move_file)
                    move_type = move_data['typename']

                    if str(move_num) in special_move_data:
                        special_move = special_move_data[str(move_num)]
                        if str(self.held_item_num) in special_move:
                            move_type = special_move[str(self.held_item_num)]

                    if str(self.ability_num) in FORCE_TYPE_ABILITIES:
                        ability_data = FORCE_TYPE_ABILITIES[str(self.ability_num)]
                        if move_type == ability_data['forced_from']:
                            move_type = ability_data['forced_type']
                        elif ability_data['forced_from'] == '*':
                            move_type = ability_data['forced_type']
                    move_data_res = dict(
                        move_name=move_data['movename'],
                        max_pp=move_data['movepp'],
                        type=move_type,
                        power=int(move_data['movepower']),
                        accuracy=int(move_data['moveaccuracy']),
                        category=move_data['movecategoryname']
                    )
                    yield move_num

        self.moves = [move for move in moves(self)]

        with open('data/mon_data.json') as mon_file, open('data/pokemon_forms.json') as forms_file:
            pokemon_data = json.load(mon_file)
            general_forms_data = json.load(forms_file)
            try:
                if str(self.dex_number) in general_forms_data:
                    this_pokemon_data = general_forms_data[str(self.dex_number)]
                    if str(self.form) in this_pokemon_data:
                        pokemon_form_data = this_pokemon_data[str(self.form)]
                    else:
                        pokemon_form_data = this_pokemon_data['0']
                else:
                    pokemon_form_data = pokemon_data[str(self.dex_number)]['0']
            except:
                pokemon_form_data = pokemon_data[str(self.dex_number)]['0']
            try:
                self.species = pokemon_form_data['name']
            except:
                if '0' in pokemon_data[str(self.dex_number)]:
                    species = pokemon_data[str(self.dex_number)]['0']['name']
                    suffix = pokemon_form_data
                    self.species = f'{species} {suffix}'
                    pokemon_form_data = pokemon_data[str(self.dex_number)][suffix]
                else:
                    self.form = pokemon_form_data
                    pokemon_form_data = pokemon_data[str(self.dex_number)][pokemon_form_data]
                    self.species = pokemon_form_data['name']

            self.types = [{'name': value['name'].lower()} for value in pokemon_form_data['types']]

        with open('data/ability_data.json') as ability_file, open('data/nature_data.json') as nature_file, open(
                'data/item_data.json') as item_file:
            ability_data = json.load(ability_file)
            nature_data = json.load(nature_file)
            item_data = json.load(item_file)
            self.ability_name = ability_data[str(self.ability_num)]['name']
            self.nature_name = nature_data[str(self.nature_num)]['name']
            self.item_name = item_data[str(self.held_item_num)]['name']

    def to_dict(self):
        if self.dex_number == 0:
            return None
        return dict(
            pid=self.pid,
            suffix=self.suffix,
            level=clamp(self.level, max_value=100),
            dex_number=self.dex_number,
            form=str(self.form),
            held_item=self.held_item_num,
            ability=self.ability_num,
            nature=self.nature_num,
            moves=self.moves,
            mote=self.mote,
            sprite_url=f'https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/{self.dex_number}.png',
            types=self.types,
            ability_name=self.ability_name,
            nature_name=self.nature_name,
            item_name=self.item_name,
            iv_hp=self.iv_hp,
            iv_attack=self.iv_attack,
            iv_defense=self.iv_defense,
            iv_speed=self.iv_speed,
            iv_spatk=self.iv_spatk,
            iv_spdef=self.iv_spdef,
            ev_hp=self.ev_hp,
            ev_attack=self.ev_attack,
            ev_defense=self.ev_defense,
            ev_speed=self.ev_speed,
            ev_spatk=self.ev_spatk,
            ev_spdef=self.ev_spdef,
        )

    def to_trained_pokemon(self):
        from pokemon_api.models import Pokemon, Item, PokemonAbility, PokemonNature
        from trainer_data.models import TrainerPokemon

        form_filter = Q(form=self.form) | Q(form=0)
        pokemon = Pokemon.objects.get(form_filter, dex_number=self.dex_number)
        held_item = Item.objects.get(index=self.held_item_num)
        ability = PokemonAbility.objects.get(index=self.ability_num)
        nature = PokemonNature.objects.get(index=self.nature_num)
        pkmn = TrainerPokemon(
            pokemon=pokemon,
            mote=self.mote,
            form=self.form,
            held_item=held_item,
            ability=ability,
            nature=nature,
            level=self.level,
            suffix=self.suffix,
            ev_hp=self.ev_hp,
            ev_attack=self.ev_attack,
            ev_defense=self.ev_defense,
            ev_speed=self.ev_speed,
            ev_special_attack=self.ev_spatk,
            ev_special_defense=self.ev_spdef,
            iv_hp=self.iv_hp,
            iv_attack=self.iv_attack,
            iv_defense=self.iv_defense,
            iv_speed=self.iv_speed,
            iv_special_attack=self.iv_spatk,
            iv_special_defense=self.iv_spdef,
        )

        pkmn.save()


def crypt(data, seed, i):
    value = data[i]
    shifted_seed = seed >> 16
    shifted_seed &= 0xFF
    value ^= shifted_seed
    result = struct.pack("B", value)

    value = data[i + 1]
    shifted_seed = seed >> 24
    shifted_seed &= 0xFF
    value ^= shifted_seed
    result += struct.pack("B", value)

    return result


def crypt_array(data, seed, start, end):
    result = bytes()
    temp_seed = seed

    for i in range(start, end, 2):
        temp_seed *= 0x41C64E6D
        temp_seed &= 0xFFFFFFFF
        temp_seed += 0x00006073
        temp_seed &= 0xFFFFFFFF
        result += crypt(data, temp_seed, i)

    return result


def shuffle_array(data, sv, block_size):
    block_position = [[0, 0, 0, 0, 0, 0, 1, 1, 2, 3, 2, 3, 1, 1, 2, 3, 2, 3, 1, 1, 2, 3, 2, 3],
                      [1, 1, 2, 3, 2, 3, 0, 0, 0, 0, 0, 0, 2, 3, 1, 1, 3, 2, 2, 3, 1, 1, 3, 2],
                      [2, 3, 1, 1, 3, 2, 2, 3, 1, 1, 3, 2, 0, 0, 0, 0, 0, 0, 3, 2, 3, 2, 1, 1],
                      [3, 2, 3, 2, 1, 1, 3, 2, 3, 2, 1, 1, 3, 2, 3, 2, 1, 1, 0, 0, 0, 0, 0, 0]]
    result = bytes()
    for block in range(4):
        start = block_size * block_position[block][sv]
        end = start + block_size
        result += data[start:end]
    return result


def decrypt_data(encrypted_data):
    pv = struct.unpack("<I", encrypted_data[:4])[0]
    sv = ((pv >> 13) & 31) % 24

    start = 8
    end = (4 * BLOCK_SIZE) + 8

    header = encrypted_data[:8]

    # Blocks
    blocks = crypt_array(encrypted_data, pv, start, end)

    # Stats
    stats = crypt_array(encrypted_data, pv, end, len(encrypted_data))

    final_result = header + shuffle_array(blocks, sv, BLOCK_SIZE) + stats

    return final_result


def normalize_gender_symbol(char):
    # Aquí iría la lógica para normalizar el carácter
    match char:
        case '\uE08E':
            return '\u2642'
        case '\uE08F':
            return '\u2640'
    return char


def get_string(data):
    result = load_string(data)
    return ''.join(result)  # Crear una cadena con los caracteres procesados


def load_string(data):
    i = 0
    result = []
    while i < len(data):
        # Leer 2 bytes (como en ReadUInt16LittleEndian)
        value = struct.unpack('<H', data[i:i + 2])[0]  # '<H' es para little-endian, unsigned short
        if value == TERMINATOR_NULL:
            break
        result.append(normalize_gender_symbol(chr(value)))
        i += 2
    return result


def get_party_slot(data):
    pokemon_data_size = 0x104
    return data[:pokemon_data_size]


def get_party_offset(slot):
    party_memory_address = 0x14200
    pokemon_data_size = 0x104
    return party_memory_address + (pokemon_data_size * slot)


def get_party_span(data, slot):
    return data[get_party_offset(slot):]


def get_pokemon_in_slot(data, slot):
    return get_party_slot(get_party_span(data, slot))


def get_box_offset(box):
    box_address = 0x22600
    SIZE_6STORED = 232
    return box_address + (SIZE_6STORED * box * 30)


def get_box_slot_offset(box, slot):
    SIZE_6STORED = 232
    return get_box_offset(box) + (slot * SIZE_6STORED)


def get_stored_slot(data):
    SIZE_6STORED = 232
    pokemon_data = data[:SIZE_6STORED]
    data = pokemon_data
    pokemon = PokemonBytes(data, True)
    pokemon.get_atts()
    return pokemon.to_dict()


def get_box_slot(data, box_slot_offset):
    return get_stored_slot(data[box_slot_offset:])


def get_pokemon_at_box_slot(data, box, slot):
    return get_box_slot(data, get_box_slot_offset(box, slot))


def get_trainer_name(save_data):
    offset = 0x14000
    length = 0x00170

    trainer_memory_block = save_data[offset: offset + length]
    original_thrash_nick = trainer_memory_block[0x48:0x48 + 0x1A]
    trainer_name = get_string(original_thrash_nick)
    return trainer_name


def data_reader(save_data):
    offset = 0x14000
    length = 0x00170

    trainer_memory_block = save_data[offset: offset + length]
    original_thrash_nick = trainer_memory_block[0x48:0x48 + 0x1A]
    trainer_team = []
    total_boxes = range(7)
    boxes = dict()

    trainer_name = get_string(original_thrash_nick)

    for slot in range(6):
        pokemon = PokemonBytes(get_pokemon_in_slot(save_data, slot))
        pokemon.get_atts()
        trainer_team.append(pokemon.to_dict())

    for box in total_boxes:
        box_list = []
        for slot in range(30):
            pokemon = get_pokemon_at_box_slot(save_data, box, slot)
            if pokemon:
                box_list.append(dict(
                    slot=slot,
                    pokemon=pokemon
                ))

        if len(box_list) > 0:
            box_name_address = 4400 + box * 22
            data = save_data[box_name_address:box_name_address + 22]
            box_name = get_string(data)
            print(box_name_address)
            print(data)
            print(box_name)
            boxes[box] = dict(
                name=box_name,
                slots=box_list
            )

    return dict(
        boxes=boxes,
        trainer_name=trainer_name,
        team=trainer_team
    )
