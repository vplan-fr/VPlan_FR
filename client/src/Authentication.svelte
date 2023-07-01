<script>

</script>
<main>
    Signup:
    <form action="/signup" method="POST">
        <input name="nickname" id="nickname">
        <input name="pw" id="pw" type="password">
        <input type="submit">
    </form><br>
    Login: 
    <form action="/login" method="POST">
        <input name="nickname" id="nickname">
        <input name="pw" id="pw" type="password">
        <input type="submit">
    </form><br>
    <a href="/logout">Logout</a><br>
    Authorize:
    <form action="/authorize" method="POST">
        <input name="school_num" id="school_number">
        <input name="username" id="username">
        <input name="pw" id="pw" type="password">
        <input type="submit">
    </form><br>
</main>
<style lang="scss">

</style>