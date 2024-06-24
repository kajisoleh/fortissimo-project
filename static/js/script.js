$(document).ready(function () {
    const rowsPerPage = 5;
    let currentPage = 1;
    const $tableBody = $('#tableBody');
    const $pagination = $('#pagination');
    const $rows = $tableBody.find('tr');

    function displayTable(page) {
        $rows.hide();
        const start = (page - 1) * rowsPerPage;
        const end = start + rowsPerPage;
        $rows.slice(start, end).show();
    }

    function setupPagination() {
        $pagination.empty();
        const pageCount = Math.ceil($rows.length / rowsPerPage);

        const $prevButton = $('<li class="page-item"><button class="page-link">Prev</button></li>');
        if (currentPage === 1) $prevButton.addClass('disabled');
        $prevButton.on('click', function () {
            if (currentPage > 1) {
                currentPage--;
                displayTable(currentPage);
                setupPagination();
            }
        });
        $pagination.append($prevButton);

        for (let i = 1; i <= pageCount; i++) {
            const $button = $(`<li class="page-item"><button class="page-link">${i}</button></li>`);
            if (i === currentPage) $button.addClass('active');
            $button.on('click', function () {
                currentPage = i;
                displayTable(currentPage);
                setupPagination();
            });
            $pagination.append($button);
        }

        const $nextButton = $('<li class="page-item"><button class="page-link">Next</button></li>');
        if (currentPage === pageCount) $nextButton.addClass('disabled');
        $nextButton.on('click', function () {
            if (currentPage < pageCount) {
                currentPage++;
                displayTable(currentPage);
                setupPagination();
            }
        });
        $pagination.append($nextButton);
    }

    displayTable(currentPage);
    setupPagination();
});