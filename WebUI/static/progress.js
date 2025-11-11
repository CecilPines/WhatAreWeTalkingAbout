$(function() {
    $(".example-link").click(function(e) {
        e.preventDefault();
        let url = $(this).data("url");
        $("#search-box").val(url);
        $("#search-btn").click();
    });

    $("#search-btn").click(function() {
        let keyword = $("#search-box").val();
        if (!keyword) {
            alert("请输入搜索内容！");
            return;
        }

        $("#progress-text").text("任务启动中...");
        $("#progress-bar").css("width", "0%").text("0%");

        $.post("/run", { keyword: keyword }, function() {
            updateProgress();
        });
    });

    function updateProgress() {
        let interval = setInterval(function() {
            $.get("/progress", function(data) {
                $("#progress-bar").css("width", data.step + "%").text(data.step + "%");
                $("#progress-text").text(data.message);

                if (data.status === "done") {
                    clearInterval(interval);
                    $("#progress-text").text("任务完成，正在跳转结果页...");
                    setTimeout(() => {
                        window.location.href = "/result";
                    }, 1000);
                }
            });
        }, 500);
    }
});
