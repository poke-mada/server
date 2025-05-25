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

    if (!data.team) {
        const pkmnDiv1 = document.getElementById(`pokemon1`);
        const pkmnDiv2 = document.getElementById(`pokemon2`);
        const pkmnDiv3 = document.getElementById(`pokemon3`);
        const pkmnDiv4 = document.getElementById(`pokemon4`);
        const pkmnDiv5 = document.getElementById(`pokemon5`);
        const pkmnDiv6 = document.getElementById(`pokemon6`);

        pkmnDiv1.classList.add('d-none');
        pkmnDiv2.classList.add('d-none');
        pkmnDiv3.classList.add('d-none');
        pkmnDiv4.classList.add('d-none');
        pkmnDiv5.classList.add('d-none');
        pkmnDiv6.classList.add('d-none');
    }

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

/**
 * @param data
 *
 */
function doUpdateOverlayData(data) {
    setTimeout(() => {
        const overlay = document.getElementById(`alert-overlay`);
        overlay.classList.add('d-none')
    }, 5000)
    let audio = new Audio('https://para-mada-deploy.s3.us-east-1.amazonaws.com/pokemon-statics/overlay/laugh.mp3')
    audio.play();

    const overlay = document.getElementById(`alert-overlay`);
    overlay.classList.remove('d-none')
    const img = document.getElementById(`img-card`);
    const user = document.getElementById(`user`);
    const wildcard = document.getElementById(`wildcard-name`);
    const target = document.getElementById(`target`);

    user.innerText = data.user_name
    wildcard.innerText = data.wildcard.name
    target.innerText = data.target_name
    img.setAttribute('src', data.wildcard.sprite_src)

    console.log('updated')
}