function doUpdateData(data) {
    const gym1 = document.getElementById('gym1');
    const gym2 = document.getElementById('gym2');
    const gym3 = document.getElementById('gym3');
    const gym4 = document.getElementById('gym4');
    const gym5 = document.getElementById('gym5');
    const gym6 = document.getElementById('gym6');
    const gym7 = document.getElementById('gym7');
    const gym8 = document.getElementById('gym8');
    const deathCount = document.getElementById('death-count');

    gym1.classList.remove('bg-disabled')
    gym2.classList.remove('bg-disabled')
    gym3.classList.remove('bg-disabled')
    gym4.classList.remove('bg-disabled')
    gym5.classList.remove('bg-disabled')
    gym6.classList.remove('bg-disabled')
    gym7.classList.remove('bg-disabled')
    gym8.classList.remove('bg-disabled')

    if (!data.gym1) {
        gym1.classList.add('bg-disabled')
    }

    if (!data.gym2) {
        gym2.classList.add('bg-disabled')
    }

    if (!data.gym3) {
        gym3.classList.add('bg-disabled')
    }

    if (!data.gym4) {
        gym4.classList.add('bg-disabled')
    }

    if (!data.gym5) {
        gym5.classList.add('bg-disabled')
    }

    if (!data.gym6) {
        gym6.classList.add('bg-disabled')
    }

    if (!data.gym7) {
        gym7.classList.add('bg-disabled')
    }

    if (!data.gym8) {
        gym8.classList.add('bg-disabled')
    }
    deathCount.innerText = `x${data.deathCount}`;

    data.team.forEach((pokemon, index) => {
        const pkmnDiv = document.getElementById(`pokemon${index + 1}`);
        if (pokemon !== null) {
            pkmnDiv.classList.remove('d-none');
            pkmnDiv.children[0].src = pokemon.sprite_url;
            pkmnDiv.children[1].innerText = pokemon.mote;
        } else {
            pkmnDiv.classList.add('d-none')
        }
    })
}